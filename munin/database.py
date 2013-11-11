#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from contextlib import contextmanager
from itertools import combinations
from collections import Counter, deque
from sys import stdout

# Internal:
from munin.song import Song
from munin.utils import sliding_window, centering_window

# External:
import igraph


def _threshold_from_mean(mean_counter):
    mean, sd = mean_counter.mean, mean_counter.sd
    v = (mean + sd / 2) * (3 / 4)
    # print('|-- guessing threshold', v, ' ' * 20, mean, sd)
    return v


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

    def __iter__(self):
        return iter(self._song_list)

    def __getitem__(self, idx):
        return self._song_list[idx]

    def plot(self):
        visual_style = {}
        visual_style['vertex_label'] = [str(vx.index) for vx in self._graph.vs]
        visual_style['vertex_color'] = ['#0000AA'] * len(self._graph.vs)
        visual_style['vertex_label_color'] = ['#FFFFFF'] * len(self._graph.vs)
        visual_style['layout'] = self._graph.layout('fr')
        igraph.plot(self._graph, **visual_style)

    def find_common_attributes(self):
        counter = Counter()
        for song in self._song_list:
            counter.update(song.keys())
        print(counter.most_common())

    def _rebuild_step_base(self, mean_counter, window_size=50, step_size=25):
        # Base Iteration:
        slider = sliding_window(self._song_list, window_size, step_size)
        center = centering_window(self._song_list, window_size // 2)
        anticn = centering_window(self._song_list, window_size // 2, parallel=False)

        compute = Song.distance_compute
        add = Song.distance_add

        # Base Iteration:
        for idx, iterator in enumerate((slider, center, anticn)):
            print('|-- Applying iteration #{}: {}'.format(idx + 1, iterator))
            for window in iterator:
                for song_a, song_b in combinations(window, 2):
                    distance = compute(song_a, song_b)
                    add(song_a, song_b, distance)
                    mean_counter.add(distance.distance)

    def _rebuild_step_refine(self, mean_counter, num_passes=100):
        add = Song.distance_add
        dfn = Song.distance_compute

        for n_iteration in range(num_passes):
            print('.', end='')
            stdout.flush()
            for idx, song in enumerate(self._song_list):
                result_set = deque()
                threshold = _threshold_from_mean(mean_counter)
                for ind_ngb in set(song.distance_indirect_iter(threshold)):
                    distance = dfn(song, ind_ngb)
                    result_set.append((ind_ngb, distance))
                    mean_counter.add(distance.distance)

                # Add the new distances, but only until a "worst" one was reached.
                left_enough, right_enough = False, False
                for ind_ngb, dist in sorted(result_set, key=lambda x: x[1]):
                    # if all((left_enough, right_enough)):
                    #    break

                    if not left_enough and add(song, ind_ngb, dist, bidir=False) is False:
                        left_enough = True

                    if not right_enough and add(ind_ngb, song, dist, bidir=False) is False:
                        right_enough = True
        print()

    def _rebuild_step_build_graph(self):
        self._graph = igraph.Graph()

        for song in self._song_list:
            self._graph.add_vertex(name=str(song.uid))
        # self._graph.add_vertices(len(self._song_list))

        edge_set = deque()
        for song_a in self._song_list:
            for song_b, distance in song_a.distance_iter():
                fst, snd = min(song_a.uid, song_b.uid), max(song_a.uid, song_b.uid)
                edge_set.append((fst, snd))

        self._graph.add_edges(set(edge_set))

    def rebuild(self, window_size=50, step_size=25, refine_passes=10):
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

    def add_song(self, song):
        '''Add a single song to the database.

        :returns: the added song for convinience.
        '''
        if song is not None:
            song.uid = len(self._song_list)
            self._song_list.append(song)

        return song

    def add_values(self, value_dict):
        '''Creates a song from value dict and add it to the database.

        .. seealso:: :func:`add`

        The song will be configured to the config values set in the Session.

        :returns: the added song for convinience
        '''
        for key, value in value_dict.items():
            try:
                provider = self._session.provider_for_key(key)
                value_dict[key] = provider.process(value)
            except KeyError:
                raise KeyError('key "{k}" is not in attribute mask'.format(k=key))

        return self.add_song(Song(
            self._session, value_dict,
            max_neighbors=self._session.config['max_neighbors'],
            max_distance=self._session.config['max_distance']
        ))

    @contextmanager
    def transaction(self):
        'Convienience method: Excecute block and call :func:`rebuild` afterwards.'
        yield
        self.rebuild()


if __name__ == '__main__':
    import unittest
    import sys
    from munin.session import Session
    from munin.provider import DirectProvider

    class _DummyProvider(DirectProvider):
        def __init__(self):
            DirectProvider.__init__(self, 'dummy', is_reversible=False)

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
                    # self._session.database.add_values({
                    #     'genre': 'alfonso',
                    #     'artist': ''
                    # })

            # song_a, song_b = self._session.database
            # self.assertAlmostEqual(song_a.distance_get(song_b).distance, 0.0)
            # self.assertAlmostEqual(song_b.distance_get(song_b).distance, 0.0)

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

        from random import random
        import math

        with session.database.transaction():
            N = 200
            for i in range(int(N / 2) + 1):
                # session.database.add_values({
                #     'genre': random(),
                #     'artist': 1.0 - random()
                # })
                session.database.add_values({
                    'genre': 1.0 - i / N,
                    'artist': 1.0 - i / N

                })

                # Pseudo-Random, but deterministic:
                # euler = lambda x: math.fmod(math.e ** x, 1.0)
                # session.database.add_values({
                #     'genre': euler((i + 1) % 30),
                #     'artist': euler((N - i + 1) % 30)
                # })

        print('+ Step #4: Layouting and Plotting')
        session.database.plot()

    if '--cli' in sys.argv:
        main()
    else:
        unittest.main()
