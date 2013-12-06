#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from contextlib import contextmanager
from itertools import combinations
from collections import Counter, deque
from colorsys import hsv_to_rgb
from sys import stdout
import math

# Internal:
from munin.song import Song
from munin.utils import sliding_window, centering_window
from munin.history import ListenHistory, RuleIndex

# External:
import igraph


class Database:
    'Class managing Database concerns.'
    def __init__(self, session):
        '''Usually you access this as ``.database`` attribute of
        :class:`munin.session.Session`.

        You can do the following tasks with it:

        * Add songs to the database (:func:`add`, :func:`add_values`)
        * Trigger updates (:func:`rebuild`, :func:`transaction`)
        * Iterative over the database (``for song in database``).
        * Get a song by it's uid. (``database[song.uid]``)

        .. note::

            The division of :class:`munin.session.Session` and :class:`Database`
            is purely cosmetical. Both classes cannot exist on its own.
        '''
        self._session = session
        self._song_list = []
        self._graph = igraph.Graph()

        self._revoked_uids = set()

        # TODO: Provide config options
        # TODO: Implement history (remove!)
        self._listen_history = ListenHistory()
        self._rule_index = RuleIndex()
        self._playcounts = Counter()

    def __iter__(self):
        return iter(self._song_list)

    def __getitem__(self, idx):
        return self._song_list[idx]

    def _current_uid(self):
        if len(self._revoked_uids) > 0:
            return self._revoked_uids.pop()
        return len(self._song_list)

    def feed_history(self, song):
        '''Feed a single song to the history.

        If the feeded song is not yet in the database,
        it will be added automatically.

        :param song: The song to feed in the history.
        '''
        try:
            self.lookup_song(song.uid)
        except IndexError:
            self.insert_song(song)

        if self._listen_history.feed(song):
            rules = self._listen_history.find_rules()
            self._rule_index.insert_rules(rules)

        self._playcounts[song] += 1

    def plot(self):
        '''Plot the current graph for debugging purpose.

        Will try to open an installed image viewer.
        '''
        visual_style = {}
        visual_style['vertex_label'] = [str(vx['song'].uid) for vx in self._graph.vs]

        def color_from_distance(distance):
            return '#' + '01234567890ABCDEF'[int(distance * 16)] * 2 + '0000'

        def edge_color_list():
            vs = self._graph.vs
            edge_colors, edge_widths = deque(), deque()

            for edge in self._graph.es:
                a, b = vs[edge.source]['song'], vs[edge.target]['song']
                distance = a.distance_get(b)
                if distance is not None:
                    edge_colors.append(color_from_distance(distance.distance))
                    edge_widths.append((distance.distance + 0.1) * 3)

            return list(edge_colors), list(edge_widths)

        visual_style['edge_color'], visual_style['edge_width'] = edge_color_list()
        colors = self._graph.eigenvector_centrality(directed=False)
        visual_style['vertex_color'] = [hsv_to_rgb(v, 1.0, 1.0) for v in colors]
        visual_style['vertex_label_color'] = [hsv_to_rgb(1 - v, 0.5, 1.0) for v in colors]
        visual_style['vertex_size'] = [42] * len(self._graph.vs)
        visual_style['layout'] = self._graph.layout('fr')
        visual_style['bbox'] = (800, 800)
        igraph.plot(self._graph, **visual_style)

    def _rebuild_step_base(self, mean_counter, window_size=60, step_size=20):
        '''Do the Base Iterations.

        This involves three iterations:

            * :func:`munin.utils.sliding_window`
              Window over the List (overlapping with * window_size/step_size).
            * :func:`munin.utils.centering_window` with `parallel=True`.
            * :func:`munin.utils.centering_window` with `parallel=True`.

        :param mean_counter: A RunningMean counter to sample the initial mean/sd
        :param window_size: The max. size of the window in which combinations are taken.
        :param step_size: The movement of the window per iteration.
        '''
        # Base Iteration:
        slider = sliding_window(self._song_list, window_size, step_size)
        center = centering_window(self._song_list, window_size // 2)
        anticn = centering_window(self._song_list, window_size // 2, parallel=False)

        # Prebind the functions for performance reasons.
        compute = Song.distance_compute
        add = Song.distance_add

        # Select the iterator:
        for idx, iterator in enumerate((slider, center, anticn)):
            print('|-- Applying iteration #{}: {}'.format(idx + 1, iterator))

            # Iterate over the list:
            for window in iterator:
                # Calculate the combination set:
                for song_a, song_b in combinations(window, 2):
                    distance = compute(song_a, song_b)
                    add(song_a, song_b, distance)

                    # Sample the newly calculated distance.
                    mean_counter.add(distance.distance)

    def _rebuild_step_refine(self, mean_counter, num_passes, mean_scale=2):
        '''Do the refinement step.

        .. seealso:: :func:`rebuild`

        :param mean_counter: RunningMean Counter
        :param num_passes: How many times the song list shall be iterated.
        '''
        # Prebind the functions for performance reasons:
        add = Song.distance_add
        dfn = Song.distance_compute

        # Do the whole thing `num_passes` times...
        for n_iteration in range(num_passes):
            print('.', end='')
            stdout.flush()

            threshold = (mean_counter.mean * mean_scale - mean_counter.sd) / mean_scale
            newly_found = 0

            # Go through the song_list...
            for idx, song in enumerate(self._song_list):
                # ..and remember each calculated distance
                # we got from compare the song with its indirect neighbors.
                result_set = deque()

                # Iterate over the indirect neighbors (those having a certain
                # distance lower than threshold):
                for ind_ngb in set(song.distance_indirect_iter(threshold)):
                    distance = dfn(song, ind_ngb)
                    result_set.append((ind_ngb, distance))
                    mean_counter.add(distance.distance)

                # Add the distances (we should not do this during # iteration)
                # Also count which of these actually
                for ind_ngb, dist in result_set:
                    newly_found += add(song, ind_ngb, dist)

            # Stop iteration when not enough new distances were gathered
            # (at least one new addition per song)
            # This usually only triggers for high num_passes
            if newly_found < len(self._song_list) // 2:
                print('o [not enough additions, breaking]', end='')
                break
        print()

    def _rebuild_step_build_graph(self):
        '''Built an actual igraph.Graph from the songlist.

        This is done by iteration over the songlist and gathering all
        deduplicated edges.

        The resulting graph will be stored in self._graph and will have
        len(self._song_list) vertices.
        '''
        # Create the actual graph:
        self._graph = igraph.Graph(directed=False)

        for song in self._song_list:
            self._graph.add_vertex(song=song)

        # Gather all edges in one container
        # (this speeds up adding edges)
        edge_set = deque()
        for song_a in self._song_list:
            # print(len(song_a._dist_pool))
            for song_b, _ in song_a.distance_iter():
                if song_a.distance_get(song_b) is None or song_b.distance_get(song_a) is None:
                    continue

                # Make Edge Deduplication work:
                if song_a.uid < song_b.uid:
                    edge_set.append((song_b.uid, song_a.uid))
                else:
                    edge_set.append((song_a.uid, song_b.uid))

        # Filter duplicate edge pairs.
        self._graph.add_edges(set(edge_set))

    def rebuild(self, window_size=60, step_size=20, refine_passes=25):
        '''Rebuild all distances and the associated graph.

        This will be triggered for you automatically after a transaction.
        '''
        # Average and Standard Deviation Counter:
        mean_counter = igraph.statistics.RunningMean()

        print('+ Step #1: Calculating base distance (sliding window)')
        self._rebuild_step_base(
                mean_counter,
                window_size=window_size,
                step_size=step_size
        )

        print('|-- Mean Distane: {:f} (sd: {:f})'.format(mean_counter.mean, mean_counter.sd))
        print('+ Step #2: Applying refinement:', end='')
        self._rebuild_step_refine(
            mean_counter,
            num_passes=refine_passes
        )

        print('|-- Mean Distane: {:f} (sd: {:f})'.format(mean_counter.mean, mean_counter.sd))
        print('+ Step #3: Building Graph')
        self._rebuild_step_build_graph()

    def add_values(self, value_dict):
        '''Creates a song from value dict and add it to the database.

        .. seealso:: :func:`add`

        The song will be configured to the config values set in the Session.

        :returns: the added song for convinience
        '''
        for key, value in value_dict.items():
            try:
                provider = self._session.provider_for_key(key)
                if value is None:
                    value_dict[key] = None
                else:
                    value_dict[key] = provider.process(value)
            except KeyError:
                raise KeyError('key "{k}" is not in attribute mask'.format(k=key))

        new_song = Song(
            self._session, value_dict,
            max_neighbors=self._session.config['max_neighbors'],
            max_distance=self._session.config['max_distance']
        )

        new_song.uid = self._current_uid()
        self._song_list.append(new_song)
        return new_song.uid

    @contextmanager
    def transaction(self):
        'Convienience method: Excecute block and call :func:`rebuild` afterwards.'
        with self.fixing():
            yield
            self.rebuild()

    @contextmanager
    def fixing(self):
        yield

        for song in self._song_list:
            song.distance_finalize()

            # This is just some sort of assert and has no functionality:
            last = None
            for other, dist in song.distance_iter():
                if last is not None and last > dist:
                    print('!! warning: unsorted elements: !({} < {})'.format(dist, last))
                last = dist

    def lookup_song(self, uid):
        '''Lookup a certain song by it's uid.

        :param uid: A uid previously given by
        :returns: a :class:`munin.song.Song`, which is a read-only mapping of normalized attributes.
        '''
        try:
            return self._song_list[uid]
        except IndexError:
            raise IndexError('song uid #{} is not valid'.format(uid))

    def insert_song(self, value_dict, star_threshold=0.75):
        '''Insert a song to the database without doing a rebuild.

        This works by iterating partially over the songlist, trying to find
        a suitable point to insert it. If a distance to a random song is
        over ``star_threshold``, also the neighbors of this song is
        investigated.

        Songs inserted this way tend to have wider connections than normal
        songs, which may enrich the graph.

        :param value_dict: Same as for :func:`add_values`.
        :param star_threshold: Also consider neighbors for songs with a
                               distance higher than this.
        :returns: The uid of this new song.
        '''
        new_song = self._song_list[self.add_values(value_dict)]
        iterstep = max(1, math.log(len(self._song_list) or 1))

        distances = deque()
        for song in self._song_list[::iterstep]:
            distance = Song.distance_compute(song, new_song)
            distances.append((song, distance))
            new_song.distance_add(song, distance)

        for song, distance in distances:
            if distance.distance > star_threshold:
                for neighbor in song.neighbors():
                    distance = new_song.distance_compute(neighbor)
                    new_song.distance_add(neighbor, distance)

        return new_song.uid

    def remove_song(self, uid):
        '''Delete a single song from the graph without rebuilding it.

        Holes that may be created will be tried to be patched by connecting
        the neighbors to each other.

        :param ui: The uid of the song to delete.
        :returns: The uid you passed in for convienience.
        '''
        if len(self._song_list) <= uid:
            raise ValueError('Invalid UID #{}'.format(uid))

        song = self._song_list.pop(uid)
        self._revoked_uids.add(uid)

        # Patch the hole:
        song.disconnect()

        return uid

###########################################################################
#                               Test Stuff                                #
###########################################################################

if __name__ == '__main__':
    import unittest
    import sys
    from munin.session import Session
    from munin.provider import Provider

    class _DummyProvider(Provider):
        def __init__(self):
            Provider.__init__(self, 'dummy', is_reversible=False)

        def process(self, input_value):
            return (input_value, )

    class DatabaseTests(unittest.TestCase):
        def setUp(self):
            self._session = Session('session_test', {
                'genre': (_DummyProvider(), None, 0.2),
                'artist': (_DummyProvider(), None, 0.3)
            }, path='/tmp')

        def test_basics(self):
            with self._session.database.transaction():
                N = 200
                for i in range(N):
                    self._session.database.add_values({
                        'genre': i / N,
                        'artist': i / N
                    })

        def test_no_match(self):
            with self.assertRaisesRegex(KeyError, '.*attribute mask.*'):
                self._session.database.add_values({
                    'not_in_session': 42
                })

    def main():
        from munin.distance import DistanceFunction

        class _DummyDistance(DistanceFunction):
            def compute(self, list_a, list_b):
                return abs(list_a[0] - list_b[0])

        dprov = _DummyProvider()
        dfunc = _DummyDistance(dprov)
        session = Session('session_test', {
            'genre': (dprov, dfunc, 0.2),
            'artist': (dprov, dfunc, 0.3)
        }, path='/tmp')

        import math

        with session.database.transaction():
            N = 50
            for i in range(int(N / 2) + 1):
                session.database.add_values({
                    'genre': 1.0 - i / N,
                    'artist': 1.0 - i / N
                })
                # Pseudo-Random, but deterministic:
                euler = lambda x: math.fmod(math.e ** x, 1.0)
                session.database.add_values({
                    'genre': euler((i + 1) % 30),
                    'artist': euler((N - i + 1) % 30)
                })

        from munin.graph import recomnendations_from_song_sorted
        base = session.database._song_list[10]
        print([(song.uid, depth, base.distance_get(song, 1.0)) for song, depth in recomnendations_from_song_sorted(session.database._graph, base, n=20)])

        print('+ Step #4: Layouting and Plotting')
        session.database.plot()

    if '--cli' in sys.argv:
        main()
    else:
        unittest.main()
