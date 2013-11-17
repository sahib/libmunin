#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from bisect import bisect, insort
from collections import Hashable
from logging import getLogger
LOGGER = getLogger(__name__)

# Internal:
from munin.distance import Distance
from munin.utils import SessionMapping, float_cmp

# External:
from blist import sortedset


class Song(SessionMapping, Hashable):
    # Note: Use __slots__ (sys.getsizeof will report even more memory, but pympler less)
    __slots__ = ('_dist_dict', '_dist_pool', '_max_distance', '_max_neighbors', '_hash', '_confidence', 'uid')
    '''
    **Overview**

    A song is a readonly mapping of keys to values (like a readonly dict).

    The keys will depend on the attribute mask in the session.
    The values will be passed as value_dict to the constructor.
    Keys that are no in value_dict, but in the attribute_mask (therefore valid)
    will return the default_value passed (usually that is None).

    Internally a list is used to store the values, leaving the keys in the
    Session objects - for many instances this saves a considerable amount
    of memory.

    .. todo:: Make some numbers up to prove this :-)

    **Reference**
    '''
    def __init__(self, session, value_dict, max_neighbors=100, max_distance=0.999, default_value=None):
        '''Creates a Song (a set of attributes) that behaves like a dictionary:

        :param session: A Session objective (the session this song belongs to)
        :type session: :class:`munin.session.Session`
        :param value_dict: A mapping from the keys to the values you want to set.
        :type value_dict: Mapping
        :param default_value: The value to be returned for valid but unset keys.
        :param max_neighbors: max. numbers of neighbor-distances to save.
        :type neighbor: positive int
        :param max_distance: The minimal distance for :func:`distance_add` -
                             You should try to keep this small (i.e. to only
                             filter 1.0 distances)
        :type max_distance: float
        '''
        # Make sure the list is as long as the attribute_mask
        SessionMapping.__init__(
                self, session,
                input_dict=value_dict,
                default_value=default_value
        )
        self._dist_dict = {}
        self._dist_pool = sortedset(key=lambda e: self._dist_dict[e])

        # Settings:
        self._max_neighbors = max_neighbors
        self._max_distance = max_distance

        # Update hash on creation
        self._update_hash()

        self.uid = None

    #######################
    #  Other convinience  #
    #######################

    def __hash__(self):
        return self._hash

    def __repr__(self):
        return '<Song(uid={uid} values={val}, distances={dst})>'.format(
                val=self._store,
                uid=self.uid,
                dst={song: self._dist_dict[song] for song, dist in self._dist_pool}
        )

    ############################
    #  Distance Relations API  #
    ############################

    def distance_compute(self, other_song):
        '''Compute the distance to another song.

        This is a method of :class:`Song` and not a static method for convinience.
        If you need a static method do this: ``Song.distance_compute(s1, s2)``.

        :param other_song: a :class:`munin.song.Song`
        :returns: A :class:`munin.distance.Distance` with according weighting.
        '''
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

    def distance_add(self, other, distance, _bidir=True):
        '''Add a relation to ``other_song`` with a certain distance.

        .. warning::

            This function has linear complexity since it needs to find the
            worst element in case of a deletion.

        :param next: The song to add a relation to. Will also add a
                     relation in other_song to self with same Distance.
        :type next: :class:`munin.song.Song`
        :param distance: The Distance to add to the "edge".
        :type distance: :class:`munin.distance.Distance`
        :returns: *False* if the song was not added because of a bad distance.
                  *True* in any other case.
        '''
        # self-referencing is not allowed, also filter max_distance:
        if self is other or self._max_distance < distance.distance:
            return False

        # Check if there was already an distance for this combination.
        # If so, check if the new one is lower. If not just deny it.
        sdd, odd = self._dist_dict, other._dist_dict
        old_dist = sdd.get(other)
        if old_dist is not None and old_dist < distance:
            return False

        # Insert or update the new reference:
        sdd[other] = odd[self] = distance

        # Oh, hey, we're done already!
        if old_dist is not None:
            return True

        # Pre-bind variables:
        sdp, odp = self._dist_pool, other._dist_pool
        n, pop_self, pop_other = self._max_neighbors, False, False

        # check if we need to reduce size of other song:
        if len(odp) is n:
            if odd[odp[-1]] < distance:
                return False
            pop_other = True

        # same for our own song:
        if len(sdp) is n:
            if sdd[sdp[-1]] < distance:
                return False
            pop_self = True

        # Actually delete the items now:
        if pop_other is True:
            worst = odp.pop()
            if worst is not self:
                del odd[worst]

        if pop_self is True:
            worst = sdp.pop()
            if worst is not other:
                del sdd[worst]

        # We're almost done! Just add the new songs to the sorted set:
        sdp.add(other)
        odp.add(self)
        return True

    def distance_get(self, other_song, default_value=None):
        '''Return the distance to the song ``other_song``

        :param other_song: The song to lookup the relation to.
        :param default_value: The default value to return (default to None)
        :returns: A Distance.
        '''
        if self is other_song:
            return self.distance_compute(self)
        else:
            return self._dist_dict.get(other_song, default_value)

    def distance_len(self):
        return len(self._dist_pool)

    def distance_iter(self):
        '''Iterate over all distances stored in this song.

        :returns: iterable that yields (song, distance) tuples.
        :rtype: generator
        '''
        for song in self._dist_pool:
            yield song, self._dist_dict[song]

    def distance_indirect_iter(self, dist_threshold):
        '''Iterate over the indirect neighbors of this song.

        :returns: an generator that yields one song at a time.
        '''
        for song, dist in self.distance_iter():
            curr_dist = dist.distance
            if curr_dist < dist_threshold:
                for ind_song, ind_dist in song.distance_iter():
                    if (ind_dist.distance + curr_dist) / 2 < dist_threshold:
                        yield song

    #################################
    #  Additional helper functions  #
    #################################

    def to_dict(self):
        'Shortcut for ``dict(iter(song))``'
        return dict(iter(song))

    #############
    #  Private  #
    #############

    def _update_hash(self):
        self._hash = hash(tuple(self._store)) + id(self)


###########################################################################
#                            Ifmain Unittests                             #
###########################################################################

if __name__ == '__main__':
    import unittest
    from munin.session import Session

    # Mock the distance class
    class DistanceDummy:
        def __init__(self, d):
            self.distance = d

        def __eq__(self, other):
            return self.distance == other.distance

        def __lt__(self, other):
            return self.distance > other.distance

        def __repr__(self):
            return str(self.distance)

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
            with self._session.database.transaction():
                # Pseudo-Random, but deterministic:
                import math
                euler = lambda x: math.fmod(math.e ** x, 1.0)
                N = 40
                for i in range(N):
                    self._session.database.add_values({
                        'genre': euler(i + 1),
                        'artist': euler(N - i + 1)
                    })

            # for song in self._session.database:
            #     print(song.uid)
            #     for ind_ngb in set(song.distance_indirect_iter(1.0)):
            #         print('    ', ind_ngb.uid)

        def test_song_add(self):
            song_one = Song(self._session, {
                'genre': 'alpine brutal death metal',
                'artist': 'herbert'
            }, max_neighbors=5)

            N = 100

            for off in (0, 1.0):
                for i in range(N):
                    song_one.distance_add(Song(self._session, {
                        'genre': str(i),
                        'artist': str(i)
                    }, max_neighbors=5), DistanceDummy(off - i / N))

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

            song_one.distance_add(song_two, DistanceDummy(0.7))
            song_one.distance_add(song_one, DistanceDummy(421))  # this should be clamped to 1
            self.assertEqual(song_one.distance_get(song_one), DistanceDummy(0.0))
            self.assertEqual(song_one.distance_get(song_two), DistanceDummy(0.7))

            # Check if max_distance works correctly
            prev_len = song_one.distance_len()
            song_one.distance_add(song_two, DistanceDummy(1.0))
            self.assertEqual(song_one.distance_len(), prev_len)

            # Test "only keep the best songs"
            song_base = Song(self._session, {
                'genre': 0,
                'artist': 0
            })

            N = 200
            for idx in range(1, N + 1):
                song = Song(self._session, {
                    'genre': str(idx - 1),
                    'artist': str(idx - 1)
                })
                song_base.distance_add(song, DistanceDummy((idx - 1) / N))

            values = sorted(song_base.distance_iter(), key=lambda x: x[1])
            self.assertAlmostEqual(values[+0][1].distance, (N - 1) / N)
            self.assertAlmostEqual(values[-1][1].distance, 0.5)

    unittest.main()
