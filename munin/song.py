#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from collections import Hashable, OrderedDict, deque
from itertools import combinations
from operator import itemgetter
from logging import getLogger
LOGGER = getLogger(__name__)

# Internal:
from munin.distance import Distance
from munin.helper import SessionMapping

# External:
from blist import sortedlist


class Song(SessionMapping, Hashable):
    # Note: Use __slots__ (sys.getsizeof will report even more memory, but pympler less)
    __slots__ = ('_dist_dict', '_pop_list', '_max_distance', '_max_neighbors', '_hash', '_confidence', 'uid')
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
    def __init__(self, session, value_dict, max_neighbors=10, max_distance=0.999, default_value=None):
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
        self._dist_dict = OrderedDict()

        # make lookup local:
        d = self._dist_dict

        # Make sure bad and nonexisting songs goes to the end:
        self._pop_list = sortedlist(key=lambda x: ~d[x])

        # Settings:
        self._max_neighbors = max_neighbors
        self._max_distance = max_distance
        self.uid = None

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
        '''Like :func:`distance_iter`, but only return the neighbor song, not the distance'''
        return self._dist_dist.keys()

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

    def distance_add(self, other, distance):
        '''Add a relation to ``other_song`` with a certain distance.

        .. warning::

            This function has linear complexity since it needs to find the
            worst element in case of a deletion.

        :param other: The song to add a relation to. Will also add a
                     relation in other_song to self with same Distance.
        :type other: :class:`munin.song.Song`
        :param distance: The Distance to add to the "edge".
        :type distance: :class:`munin.distance.Distance`
        :returns: *False* if the song was not added because of a bad distance.
                  *True* in any other case.
        '''
        if other is self:
            return False

        sdd, odd = self._dist_dict, other._dist_dict
        if other in sdd:
            if sdd[other] < distance:
                return False  # Reject

            # Explain why this could damage worst song detection.
            # and why we do not care.
            sdd[other] = odd[self] = distance
            return True
        elif distance.distance <= self._max_distance:
            # Check if we still have room left
            if len(sdd) >= self._max_neighbors:
                # Find the worst song in the dictionary
                idx = 1
                for worst_song in self._pop_list:
                    if worst_song in sdd:
                        break
                    idx += 1

                if sdd[worst_song] < distance:
                    # we could prune pop_list here too,
                    # but it showed that one operation only is more effective.
                    return False

                # delete the worst one to make place,
                # BUT: do not delete the connection from worst to self
                # we create unidir edges here on purpose.
                del sdd[worst_song]
                del self._pop_list[idx + 1:]
        else:
            return False

        # Add the new element:
        sdd[other] = odd[self] = distance
        self._pop_list.add(other)
        other._pop_list.add(self)
        return True

    def distance_finalize(self):
        to_delete = deque()
        for other in self._dist_dict:
            dist_a, dist_b = self.distance_get(other), other.distance_get(self)
            if dist_a is None:
                to_delete.append((other, self))
            if dist_b is None:
                to_delete.append((self, other))

        for source, target in to_delete:
            del source._dist_dict[target]

        self._dist_dict = OrderedDict(sorted(self._dist_dict.items(), key=itemgetter(1)))

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
        return len(self._dist_dict)

    def distance_iter(self):
        '''Iterate over all distances stored in this song.

        Will yield songs with smallest distance first.

        :returns: iterable that yields (song, distance) tuples.
        :rtype: generator
        '''
        return self._dist_dict.items()

    def distance_indirect_iter(self, dist_threshold=1.1):
        '''Iterate over the indirect neighbors of this song.

        :returns: an generator that yields one song at a time.
        '''
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
        '''Deletes all edges to other songs and tries to fill the resulting hole.

        Filling the hole that may be created is by comparing it's neighbors
        with each other and adding new distances.
        '''
        # Step 1: Find new distances:
        neighbors = list(self._dist_dict.keys())
        for neighbor in neighbors:
            neighbor._max_distance += 1

        for neigh_a, neigh_b in combinations(neighbors):
            distance = Song.distance_compute(neigh_a, neigh_b)
            Song.distance_add(neigh_a, neigh_b, distance)

        for neighbor in neighbors:
            neighbor._max_distance -= 1

        # Step 2: Delete the connection to the self:
        for neigbor in neighbors:
            del self._dist_dict[neighbor]
            del neigbor._dist_dict[self]

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
                    self._session.database.add({
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

            values = list(song_base.distance_iter())
            # TODO
            # self.assertAlmostEqual(values[+0][1].distance, (N - 1) / N)
            # self.assertAlmostEqual(values[-1][1].distance, 0.5)

    unittest.main()
