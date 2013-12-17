#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from collections import Hashable, OrderedDict, deque
from itertools import combinations
from operator import itemgetter
from heapq import heappush, heappop, heapify

from logging import getLogger
LOGGER = getLogger(__name__)

# Internal:
from munin.distance import Distance
from munin.helper import SessionMapping


class Song(SessionMapping, Hashable):
    # Note: Use __slots__ (sys.getsizeof will report even more memory, but pympler less)
    __slots__ = ('_dist_dict', '_pop_list', '_max_distance', '_max_neighbors',
                 '_hash', '_confidence', 'uid', '_worst_cache')
    """
    **Overview**

    A song is a readonly mapping of keys to values (like a readonly dict).

    The keys will depend on the mask in the session.
    The values will be passed as value_dict to the constructor.
    Keys that are no in value_dict, but in the mask (therefore valid)
    will return the default_value passed (usually that is None).

    Internally a list is used to store the values, leaving the keys in the
    Session objects - for many instances this saves a considerable amount
    of memory.

    **Reference**
    """
    def __init__(self, session, value_dict, max_neighbors=None, max_distance=None):
        """Creates a Song (a set of attributes) that behaves like a dictionary:

        :param session: A Session objective (the session this song belongs to)
        :type session: :class:`munin.session.Session`
        :param value_dict: A mapping from the keys to the values you want to set.
        :type value_dict: Mapping
        :param max_neighbors: max. numbers of neighbor-distances to save.
        :type neighbor: positive int
        :param max_distance: The minimal distance for :func:`distance_add` -
                             You should try to keep this small (i.e. to only
                             filter 1.0 distances)
        :type max_distance: float
        """
        # Make sure the list is as long as the mask
        SessionMapping.__init__(
            self, session,
            input_dict=value_dict,
            default_value=None
        )
        self._dist_dict = OrderedDict()
        self._reset_invariants()

        # Settings:
        self._max_neighbors = max_neighbors or session.config['max_neighbors']
        self._max_distance = max_distance or session.config['max_distance']
        self.uid = None

    def _reset_invariants(self):
        self._worst_cache = None
        self._pop_list = [(1.0 - dist.distance, song) for song, dist in self._dist_dict.items()]
        heapify(self._pop_list)

    #######################
    #  Other convinience  #
    #######################

    def __lt__(self, other):
        return id(self) < id(other)

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return '<Song(uid={uid} values={val}, distances={dst})>'.format(
            val=self._store,
            uid=self.uid,
            dst=['{}: {}'.format(song.uid, dist) for song, dist in self._dist_dict.items()]
        )

    ############################
    #  Distance Relations API  #
    ############################

    def neighbors(self):
        """Like :func:`distance_iter`, but only return the neighbor song, not the distance"""
        return self._dist_dict.keys()

    def distance_compute(self, other_song):
        """Compute the distance to another song.

        This is a method of :class:`Song` and not a static method for convinience.
        If you need a static method do this: ``Song.distance_compute(s1, s2)``.

        :param other_song: a :class:`munin.song.Song`
        :returns: A :class:`munin.distance.Distance` with according weighting.
        """
        distance_dict = {}
        common_keys = set(self.keys()).intersection(other_song.keys())

        for key in common_keys:
            distance_func = self._session.distance_function_for_key(key)
            value_a, value_b = self[key], other_song[key]
            if value_a is None or value_b is None:
                distance_dict[key] = 1.0
            else:
                distance_dict[key] = distance_func(value_a, value_b)

        return Distance(self._session, distance_dict)



    def distance_add(self, other, distance):
        """Add a relation to ``other`` with a certain distance.

        :param other: The song to add a relation to. Will also add a
                     relation in other_song to self with same Distance.
        :type other: :class:`munin.song.Song`
        :param distance: The Distance to add to the "edge".
        :type distance: :class:`munin.distance.Distance`
        :returns: *False* if the song was not added because of a worse distance.
                  *True* in any other case.
        """
        if other is self:
            return False

        if self._worst_cache is not None and self._worst_cache < distance.distance:
            return False

        if distance.distance > self._max_distance:
            return False

        sdd, odd = self._dist_dict, other._dist_dict
        if other in sdd:
            if sdd[other] < distance:
                return False  # Reject

            # Explain why this could damage worst song detection.
            # and why we do not care. (might change sorting)
            self._worst_cache = None
            sdd[other] = odd[self] = distance
            return True

        # Check if we still have room left
        if len(sdd) >= self._max_neighbors:
            # Find the worst song in the dictionary
            while 1:
                inversion, worst_song = self._pop_list[0]
                if worst_song in sdd:
                    worst_dist = 1.0 - inversion
                    break
                heappop(self._pop_list)

            if worst_dist < distance.distance:
                # we could prune pop_list here too,
                # but it showed that one operation only is more effective.
                self._worst_cache = worst_dist
                return False

            # delete the worst one to make place,
            # BUT: do not delete the connection from worst to self
            # we create unidir edges here on purpose.
            del sdd[worst_song]
            heappop(self._pop_list)

        # Add the new element:
        sdd[other] = odd[self] = distance

        inversion = ~distance
        heappush(self._pop_list, (inversion, other))
        heappush(other._pop_list, (inversion, self))

        # Might be something different now:
        self._worst_cache = None
        return True

    def distance_finalize(self):
        """Delete/Fix all invalid edges and neighbors of this song"""
        to_consider = deque()
        for other in self._dist_dict:
            dist_a, dist_b = self.distance_get(other), other.distance_get(self)
            if dist_a is None:
                to_consider.append((other, self))
            if dist_b is None:
                to_consider.append((self, other))

        for source, target in to_consider:
            count = 0
            for other in self.neighbors():
                dist_a, dist_b = self.distance_get(other), other.distance_get(self)
                if dist_a is None or dist_b is None:
                    continue
                count += 1

            if count < self._max_neighbors:
                target._dist_dict[source] = source.distance_get(target)
            else:
                del source._dist_dict[target]

        self._dist_dict = OrderedDict(sorted(self._dist_dict.items(), key=itemgetter(1)))
        self._reset_invariants()

    def distance_get(self, other_song, default_value=None):
        """Return the distance to the song ``other_song``

        :param other_song: The song to lookup the relation to.
        :param default_value: The default value to return (default to None)
        :returns: A Distance.
        """
        if self is other_song:
            return self.distance_compute(self)
        else:
            return self._dist_dict.get(other_song, default_value)

    def distance_len(self):
        return len(self._dist_dict)

    def distance_iter(self):
        """Iterate over all distances stored in this song.

        Will yield songs with smallest distance first.

        :returns: iterable that yields (song, distance) tuples.
        :rtype: generator
        """
        return self._dist_dict.items()

    def distance_indirect_iter(self, dist_threshold=1.1):
        """Iterate over the indirect neighbors of this song.

        :returns: an generator that yields one song at a time.
        """
        # Iterate over the *sorted* set.
        for song, curr_dist in self._dist_dict.items():
            if curr_dist.distance < dist_threshold:
                for ind_song, ind_dist in song._dist_dict.items():
                    if (ind_dist.distance + curr_dist.distance) / 2 < dist_threshold:
                        yield song
                    else:
                        break
            else:
                break

    def disconnect(self):
        """Deletes all edges to other songs and tries to fill the resulting hole.

        Filling the hole that may be created is done by comparing it's neighbors
        with each other and adding new distances.
        """
        # Step 1: Find new distances:
        neighbors = list(self._dist_dict.keys())
        for neighbor in neighbors:
            neighbor._max_distance += 1

        for neigh_a, neigh_b in combinations(neighbors, 2):
            distance = Song.distance_compute(neigh_a, neigh_b)
            Song.distance_add(neigh_a, neigh_b, distance)

        for neighbor in neighbors:
            neighbor._max_distance -= 1

        # Step 2: Delete the connection to the self:
        for neighbor in neighbors:
            del self._dist_dict[neighbor]
            del neighbor._dist_dict[self]

        # Clear the old sortedlist, while we're on it..
        del self._pop_list[:]

    #################################
    #  Additional helper functions  #
    #################################

    def to_dict(self):
        'Shortcut for ``dict(iter(song))``'
        return dict(iter(self))


###########################################################################
#                            Ifmain Unittests                             #
###########################################################################

if __name__ == '__main__':
    import unittest
    from munin.session import Session
    from munin.testing import DistanceDummy

    class SongTests(unittest.TestCase):
        def setUp(self):
            self._session = Session('test', {
                'genre': (None, None, 0.1),
                'artist': (None, None, 0.1)
            })

        def test_song_basic_mapping(self):
            song = Song(self._session, {
                'genre': 'alpine brutal death metal',
                'artist': 'Herbert'
            })

            self.assertTrue(song.get('artist') == song['artist'] == 'Herbert')
            with self.assertRaises(TypeError):
                del song['genre']

        def test_song_missing_attr(self):
            # This should already fail at creation:
            with self.assertRaises(KeyError):
                song = Song(self._session, {'a': 'b'})

            song = Song(self._session, {'genre': 'berta'})

            with self.assertRaises(KeyError):
                song['berta']

            self.assertEqual(song.get('berta'), song.get('barghl'))

        def test_song_iter(self):
            input_dict = {
                'genre': 'alpine brutal death metal',
                'artist': 'Herbert'
            }

            song = Song(self._session, input_dict)
            self.assertEqual(
                    dict(iter(song)),
                    input_dict
            )

            self.assertEqual(dict(iter(song.items())), input_dict)
            self.assertEqual(set(song.keys()), set(['genre', 'artist']))
            self.assertEqual(
                set(song.values()),
                set(['alpine brutal death metal', 'Herbert'])
            )

        def test_song_distance_indirect_iter(self):
            with self._session.transaction():
                # Pseudo-Random, but deterministic:
                import math
                euler = lambda x: math.fmod(math.e ** x, 1.0)
                N = 40
                for i in range(N):
                    self._session.add({
                        'genre': euler(i + 1),
                        'artist': euler(N - i + 1)
                    })

        def test_song_add(self):
            song_one = Song(self._session, {
                'genre': 'alpine brutal death metal',
                'artist': 'herbert'
            }, max_neighbors=5)

            N = 100

            for off in (False, True):
                for i in range(N):
                    v = i / N
                    if off:
                        v = 1.0 - v
                    song_one.distance_add(Song(self._session, {
                        'genre': str(i),
                        'artist': str(i)
                    }, max_neighbors=5), DistanceDummy(v))

                self.assertEqual(len(list(song_one.distance_iter())), 5)

        def test_distances(self):
            song_one = Song(self._session, {
                'genre': 'alpine brutal death metal',
                'artist': 'herbert'
            })
            song_two = Song(self._session, {
                'genre': 'tirolian brutal death metal',
                'artist': 'Gustl'
            })

            song_one.uid = 'base1'
            song_two.uid = 'base2'

            self.assertTrue(song_one.distance_add(song_two, DistanceDummy(0.7)))
            self.assertTrue(song_two.distance_add(song_one, DistanceDummy(0.1)))
            self.assertEqual(song_one.distance_get(song_one), DistanceDummy(0.0))
            self.assertEqual(song_two.distance_get(song_two), DistanceDummy(0.0))
            self.assertEqual(song_one.distance_get(song_two), DistanceDummy(0.1))

            # Check if max_distance works correctly
            prev_len = song_one.distance_len()
            self.assertTrue(not song_one.distance_add(song_two, DistanceDummy(1.0)))
            self.assertEqual(song_one.distance_len(), prev_len)

            # Test "only keep the best songs"
            song_base = Song(self._session, {
                'genre': 0,
                'artist': 0
            }, max_neighbors=10)

            N = 20
            for idx in range(N):
                song = Song(self._session, {
                    'genre': str(idx),
                    'artist': str(idx)
                }, max_neighbors=10)
                song.uid = idx
                song_base.distance_add(song, DistanceDummy(idx / N))

            values = list(song_base.distance_iter())
            self.assertAlmostEqual(values[+0][1].distance, 0.0)
            self.assertAlmostEqual(values[-1][1].distance, (N / 2 - 1) / N)

        def test_disconnect(self):
            def star():
                for v in ['c', 'l', 'r', 't', 'd']:
                    s = Song(self._session, {'genre': [0], 'artist': [0]})
                    s.uid = v
                    yield s

            c, l, r, t, d = star()
            self.assertTrue(c.distance_add(l, DistanceDummy(0.5)))
            self.assertTrue(c.distance_add(r, DistanceDummy(0.5)))
            self.assertTrue(c.distance_add(t, DistanceDummy(0.5)))
            self.assertTrue(c.distance_add(d, DistanceDummy(0.5)))

            c.disconnect()

            self.assertTrue(c.distance_get(l) is None)
            self.assertTrue(c.distance_get(r) is None)
            self.assertTrue(c.distance_get(t) is None)
            self.assertTrue(c.distance_get(d) is None)

            for a, b in combinations((l, r, t, d), 2):
                self.assertTrue(a.distance_get(b))
                self.assertAlmostEqual(a.distance_get(b).distance, 0.0)

    unittest.main()
