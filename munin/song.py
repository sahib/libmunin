#!/usr/bin/env python
# encoding: utf-8


from collections import Hashable
from logging import getLogger
LOGGER = getLogger(__name__)


from munin.distance import Distance
from munin.utils import SessionMapping, float_cmp


class Song(SessionMapping, Hashable):
    '''
    Overview
    --------

    A song is a readonly mapping of keys to values (like a readonly dict).

    The keys will depend on the attribute mask in the session.
    The values will be passed as value_dict to the constructor.
    Keys that are no in value_dict, but in the attribute_mask (therefore valid)
    will return the default_value passed (usually that is None).

    Internally a list is used to store the values, leaving the keys in the
    Session objects - for many instances this saves a considerable amount
    of memory.

    .. todo:: Make some numbers up to prove this :-)

    Reference
    ---------
    '''
    def __init__(self, session, value_dict, neighbors=100, max_distance=0.999, default_value=None):
        '''Creates a Song (a set of attributes) that behaves like a dictionary.

        :param session: A Session objective (the session this song belongs to)
        :type session: :class:`munin.session.Session`
        :param value_dict: A mapping from the keys to the values you want to set.
        :type value_dict: Mapping
        :param default_value: The value to be returned for valid but unset keys.
        :param neighbors: max. numbers of neighbor-distances to save.
        :type neighbor: positive int
        :param max_distance: The minimal distance for :func:`distance_add` -
                             You should try to keep this small (i.e. only
                             filter 1.0 distances)
        :type max_distance: float
        '''
        # Make sure the list is as long as the attribute_mask
        SessionMapping.__init__(
                self, session,
                input_dict=value_dict,
                default_value=default_value
        )
        self._distances = {}

        # Settings:
        self._neighbors = neighbors
        self._max_distance = max_distance

        # The worst song we have in self._distances.
        # This is used to delete it in constant time.
        self._worst_song = None

        # Update hash on creation
        self._update_hash()

    #######################
    #  Other convinience  #
    #######################

    def __hash__(self):
        return self._hash

    def __repr__(self):
        return '<Song(values={val}, distances={dst})>'.format(
                val=self._store,
                dst={hash(song): val for song, val in self._distances.items()}
        )

    ############################
    #  Distance Relations API  #
    ############################

    def distance_compute(self, other_song):
        distance_dict = {}
        common_keys = set(self.keys()) & set(other_song.keys())
        for key in common_keys:
            distance_func = self._session.distance_function_for_key(key)
            distance_dict[key] = distance_func.calculate_distance(
                    self[key],
                    other_song[key]
            )
        return Distance(self._session, distance_dict)

    def distance_add(self, other_song, distance, _bidir=True):
        '''Add a relation to ``other_song`` with a certain distance.

        :param other_song: The song to add a relation to. Will also add a
                           relation in other_song to self with same Distance.
        :type other_song: :class:`munin.song.Song`
        :param distance: The Distance to add to the "edge".
        :type distance: :class:`munin.distance.Distance`
        '''
        # Make sure that same songs always get 0.0 as distance.
        dist_value = distance.distance
        if dist_value <= self._max_distance:
            if len(self._distances) > self._neighbors:
                # delete the worst one.
                if self._worst_song is not None:
                    self._distances[self._worst_song].pop()

            # Add the relation:
            self._distances[other_song] = distance

            # Check if we've found a new worst-song:
            if self._worst_song is None or dist_value < self._distances[self._worst_song].distance:
                self._worst_song = other_song

        # Repeat procedure for the other song:
        if _bidir is True:
            other_song.distance_add(self, distance, _bidir=False)

    def distance_del(self, other_song):
        '''Delete the relation to ``other_song``

        :raises: A :class:`KeyError` if no such key exists.
        '''
        self._distances.pop(other_song)
        other_song._distances.pop(self)

    def distance_get(self, other_song, default_value=None):
        '''Return the distance to the song ``other_song``

        :param other_song: The song to lookup the relation to.
        :param default_value: The default value to return (default to None)
        :returns: A Distance.
        '''
        if self is other_song:
            return self.distance_compute(self)
        else:
            return self._distances.get(other_song, default_value)

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
        self._hash = hash(tuple(self._store))


if __name__ == '__main__':
    import unittest
    from munin.session import Session

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

        def test_distances(self):
            song_one = Song(self._session, {
                'genre': 'alpine brutal death metal',
                'artist': 'Herbert'
            })
            song_two = Song(self._session, {
                'genre': 'tirolian brutal death metal',
                'artist': 'Gustl'
            })

            class DistanceDummy:
                def __init__(self, d):
                    self.distance = d

                def __eq__(self, other):
                    return self.distance == other.distance

            song_one.distance_add(song_two, DistanceDummy(0.7))
            song_one.distance_add(song_one, DistanceDummy(421))  # this should be clamped to 1
            self.assertEqual(song_one.distance_get(song_one), DistanceDummy(0.0))
            self.assertEqual(song_one.distance_get(song_two), DistanceDummy(0.7))

            # TODO: Test neighbors and max_distance parameter.
            song_two = Song(self._session, {
                'genre': 0
                'artist': 0
            })

            N = 101
            for idx in range(1, N + 1):
                song = Song(self._session, {
                    'genre': str(idx),
                    'artist': str(idx)
                })

                song_base.distance_add(song, DistanceDummy(idx / N))



    unittest.main()
