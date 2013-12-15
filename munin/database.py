#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from itertools import combinations
from collections import Counter, deque

import math
import logging

LOGGER = logging.getLogger(__name__)

# Internal:
from munin.song import Song
from munin.helper import sliding_window, centering_window, RunningMean
from munin.history import ListenHistory, RuleIndex

import munin.plot


class Database:
    'Class managing Database concerns.'
    def __init__(self, session):
        """Usually you access this as ``.database`` attribute of
        :class:`munin.session.Session`.

        You can do the following tasks with it:

        * Trigger updates (:func:`rebuild`)
        * Get a plot of the graph for debuggin purpose.
        * Iterative over the database (``for song in database``).
        * Get a song by it's uid. (``database[song.uid]``)

        .. note::

            The division of :class:`munin.session.Session` and :class:`Database`
            is purely cosmetical. Both classes cannot exist on its own.
        """
        self._session = session
        self._song_list = []

        # TODO: Provide config options
        self._reset_history()

    def _reset_history(self):
        self._revoked_uids = set()
        self._listen_history = ListenHistory()
        self._rule_index = RuleIndex()
        self._playcounts = Counter()

    def __iter__(self):
        return filter(None, self._song_list)

    def __len__(self):
        return len(self._song_list) - len(self._revoked_uids)

    def __getitem__(self, idx):
        """Lookup a certain song by it's uid.

        :param uid: A uid previously given by
        :returns: a :class:`munin.song.Song`, which is a read-only mapping of normalized attributes.
        """
        try:
            return self._song_list[idx]
        except IndexError:
            raise IndexError('song uid #{} is invalid'.format(idx))

    def _current_uid(self):
        if self._revoked_uids:
            return self._revoked_uids.pop()
        return len(self._song_list)

    def plot(self, width=1000, height=1000):
        """Plot the current graph for debugging purpose.

        Will try to open an installed image viewer - does not return an image.

        :param database: The database (and the assoicate graph with it) to plot.
        :param width: Width of the plotted image in pixel.
        :param height: Width of the plotted image in pixel.
        """
        munin.plot.plot(self, width, height)

    def playcount(self, song):
        return self._playcounts.get(song, 0)

    def playcounts(self, n=0):
        if n < 1:
            return self._playcounts
        else:
            return self._playcounts.most_common(n)

    def feed_history(self, song):
        try:
            self[song.uid]
        except IndexError:
            self.insert(song)

        if self._listen_history.feed(song):
            rules = self._listen_history.find_rules()
            self._rule_index.insert_rules(rules)

        self._playcounts[song] += 1

    def find_matching_attributes(self, subset):
        try:
            value_set = set()
            for key, value in subset.items():
                provider = self._session.provider_for_key(key)
                value_set.add(provider.process(value))

            for song in self:
                if all((song[key] in value_set for key in subset.keys())):
                    yield song
        except KeyError:
            raise KeyError('key "{k}" is not in attribute mask'.format(k=key))

    def _rebuild_step_base(self, mean_counter, window_size=60, step_size=20):
        """Do the Base Iterations.

        This involves three iterations:

            * :func:`munin.helper.sliding_window`
              Window over the List (overlapping with * window_size/step_size).
            * :func:`munin.helper.centering_window` with `parallel=True`.
            * :func:`munin.helper.centering_window` with `parallel=True`.

        :param mean_counter: A RunningMean counter to sample the initial mean/sd
        :param window_size: The max. size of the window in which combinations are taken.
        :param step_size: The movement of the window per iteration.
        """
        # Base Iteration:
        slider = sliding_window(self, window_size, step_size)
        center = centering_window(self, window_size // 2)
        anticn = centering_window(self, window_size // 2, parallel=False)

        # Prebind the functions for performance reasons.
        compute = Song.distance_compute
        add = Song.distance_add

        # Select the iterator:
        for idx, iterator in enumerate((slider, center, anticn)):
            LOGGER.debug('|-- Applying iteration #{}: {}'.format(idx + 1, iterator))

            # Iterate over the list:
            for window in iterator:
                # Calculate the combination set:
                for song_a, song_b in combinations(window, 2):
                    distance = compute(song_a, song_b)
                    add(song_a, song_b, distance)

                    # Sample the newly calculated distance.
                    mean_counter.add(distance.distance)

    def _rebuild_step_refine(self, mean_counter, num_passes, mean_scale=2):
        """Do the refinement step.

        .. seealso:: :func:`rebuild`

        :param mean_counter: RunningMean Counter
        :param num_passes: How many times the song list shall be iterated.
        """
        # Prebind the functions for performance reasons:
        add = Song.distance_add
        compute = Song.distance_compute

        # Do the whole thing `num_passes` times...
        for n_iteration in range(num_passes):
            threshold = (mean_counter.mean * mean_scale - mean_counter.sd) / mean_scale
            newly_found = 0

            # Go through the song_list...
            for idx, song in enumerate(self):
                # ..and remember each calculated distance
                # we got from compare the song with its indirect neighbors.
                result_set = deque()

                # Iterate over the indirect neighbors (those having a certain
                # distance lower than threshold):
                for ind_ngb in set(song.distance_indirect_iter(threshold)):
                    distance = compute(song, ind_ngb)
                    result_set.append((ind_ngb, distance))
                    mean_counter.add(distance.distance)

                # Add the distances (we should not do this during # iteration)
                # Also count which of these actually
                for ind_ngb, dist in result_set:
                    newly_found += add(song, ind_ngb, dist)

            # Stop iteration when not enough new distances were gathered
            # (at least one new addition per song)
            # This usually only triggers for high num_passes
            if newly_found < len(self) // 2:
                break
        LOGGER.debug('Did {}x (of max. {}) refinement steps.'.format(n_iteration, num_passes))

    def rebuild_stupid(self):
        """(Re)build the graph by calculating the combination of all songs.

        This is a *very* expensive operation which takes quadratic time and
        only should be ever used for a small amount of songs where accuracy
        matters even more thant time.
        """
        for song_a, song_b in combinations(self._song_list, 2):
            distance = Song.distance_compute(song_a, song_b)
            Song.distance_add(song_a, song_b, distance)

    def rebuild(self, window_size=60, step_size=20, refine_passes=25, stupid_threshold=400):
        """Rebuild all distances and the associated graph.

        This will be triggered for you automatically after a transaction.

        :param int window_size: The size of the sliding window in the base iteration.
        :param int step_size: The amount to move the window per iteration.
        :param int refine_passes: How often step #2 should be repeated.
        :param int stupid_threshold: If less songs than this just brute forcely calculate all combations of songs.
        """
        if len(self) < stupid_threshold:
            LOGGER.debug('+ Step #1 + 2: Brute Force calculation due to few songs')
            self.rebuild_stupid()
        else:
            # Average and Standard Deviation Counter:
            mean_counter = RunningMean()

            LOGGER.debug('+ Step #1: Calculating base distance (sliding window)')
            self._rebuild_step_base(
                mean_counter,
                window_size=window_size,
                step_size=step_size
            )

            LOGGER.debug('|-- Mean Distane: {:f} (sd: {:f})'.format(
                mean_counter.mean, mean_counter.sd
            ))
            LOGGER.debug('+ Step #2: Applying refinement:', end='')
            self._rebuild_step_refine(
                mean_counter,
                num_passes=refine_passes
            )

            LOGGER.debug('|-- Mean Distane: {:f} (sd: {:f})'.format(
                mean_counter.mean, mean_counter.sd
            ))

        self._reset_history()

    def add(self, value_dict):
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
        if new_song.uid >= len(self._song_list):
            self._song_list.append(new_song)
        else:
            self._song_list[new_song.uid] = new_song
        return new_song.uid

    def fix_graph(self):
        for song in self:
            song.distance_finalize()

            # This is just some sort of assert and has no functionality:
            last = None
            for other, dist in song.distance_iter():
                if last is not None and last > dist:
                    LOGGER.critical('!! warning: unsorted elements: !({} < {})'.format(dist, last))
                last = dist

    def insert(self, value_dict, star_threshold=0.75, iterstep_threshold=50):
        prev_len = len(self._song_list)
        new_song = self._song_list[self.add(value_dict)]
        next_len = len(self._song_list)

        if len(self) < iterstep_threshold:
            iterstep = 1
        else:
            iterstep = round(max(1, math.log(max(next_len, 1))))

        # Step 1: Find samples with similar songs (similar to the base step)
        distances = deque()
        for song in self._song_list[::iterstep]:
            if song is not None:
                distance = Song.distance_compute(song, new_song)
                distances.append((song, distance))
                new_song.distance_add(song, distance)

        # Step 2: Short refinement step
        for song, distance in distances:
            if distance.distance > star_threshold:
                for neighbor in song.neighbors():
                    distance = new_song.distance_compute(neighbor)
                    new_song.distance_add(neighbor, distance)

        return new_song.uid

    def remove(self, uid):
        if len(self._song_list) <= uid:
            raise ValueError('Invalid UID #{}'.format(uid))

        song = self._song_list[uid]
        self._song_list[uid] = None
        self._revoked_uids.add(uid)

        edge_set = set()
        for neighbor in song.neighbors():
            edge_set.add((song.uid, neighbor.uid))

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

    class DatabaseTests(unittest.TestCase):
        def setUp(self):
            self._session = Session('session_test', {
                'genre': (None, None, 0.2),
                'artist': (None, None, 0.3)
            })

        def test_basics(self):
            with self._session.transaction():
                N = 20
                for i in range(N):
                    self._session.database.add({
                        'genre': i / N,
                        'artist': i / N
                    })

        def test_no_match(self):
            with self.assertRaisesRegex(KeyError, '.*attribute mask.*'):
                self._session.database.add({
                    'not_in_session': 42
                })

        def test_insert_remove_song(self):
            songs = []
            with self._session.transaction():
                for idx, v in enumerate(['l', 'r', 't', 'd']):
                    songs.append(self._session.add({'genre': [0], 'artist': [0]}))

            # self._session.database.plot(250, 250)
            with self._session.fix_graph():
                self._session.insert({'genre': [0], 'artist': [0]})
            # self._session.database.plot(250, 250)

            for song in self._session.database:
                for other in self._session.database:
                    if self is not other:
                        self.assertAlmostEqual(song.distance_get(other).distance, 0.0)

            self._session.remove(4)
            # self._session.database.plot(250, 250)
            with self._session.fix_graph():
                self._session.insert({'genre': [0], 'artist': [0]})
            # self._session.database.plot(250, 250)

        def test_find_matching_attributes(self):
            from munin.provider import GenreTreeProvider
            from munin.distance import GenreTreeDistance
            from munin.helper import pairup

            session = Session('session_find_test', {
                'genre': pairup(GenreTreeProvider(), GenreTreeDistance(), 5),
                'artist': pairup(None, None, 1)
            })
            session.add({
                'artist': 'Berta',
                'genre': 'death metal'
            })
            session.add({
                'artist': 'Hans',
                'genre': 'metal'
            })
            session.add({
                'artist': 'Berta',
                'genre': 'pop'
            })

            found = list(session.find_matching_attributes({'genre': 'metal'}))
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0], session[1])

            found = list(session.find_matching_attributes(
                {'genre': 'metal', 'artist': 'Berta'}
            ))
            self.assertEqual(len(found), 0)

            found = list(session.find_matching_attributes(
                {'genre': 'metal', 'artist': 'Hans'}
            ))
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0], session[1])

            found = list(session.find_matching_attributes(
                {'genre': 'pop', 'artist': 'Berta'}
            ))
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0], session[2])

            found = list(session.find_matching_attributes({'artist': 'Berta'}))
            self.assertEqual(len(found), 2)
            self.assertEqual(found[0], session[0])
            self.assertEqual(found[1], session[2])

    def main():
        from munin.testing import DummyDistanceFunction

        session = Session('session_test', {
            'genre': (None, DummyDistanceFunction(), 0.2),
            'artist': (None, DummyDistanceFunction(), 0.3)
        })

        import math
        LOGGER.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # add formatter to ch
        ch.setFormatter(
            logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        )

        # add ch to logger
        LOGGER.addHandler(ch)

        with session.transaction():
            N = 100
            for i in range(int(N / 2) + 1):
                session.add({
                    'genre': 1.0 - i / N,
                    'artist': 1.0 - i / N
                })
                # Pseudo-Random, but deterministic:
                euler = lambda x: math.fmod(math.e ** x, 1.0)
                session.database.add({
                    'genre': euler((i + 1) % 30),
                    'artist': euler((N - i + 1) % 30)
                })

        LOGGER.debug('+ Step #3: Layouting and Plotting')
        session.database.plot(3000, 3000)

    if '--cli' in sys.argv:
        main()
    else:
        unittest.main()
