#!/usr/bin/env python
# encoding: utf-8


from collections import Hashable
from munin.utils import SessionMapping
from logging import getLogger

LOGGER = getLogger(__name__)


class Song(SessionMapping, Hashable):
    '''A song is a readonly mapping of keys to values (like a readonly dict).

    The keys will depend on the attribute mask in the session.
    The values will be passed as value_dict to the constructor.
    Keys that are no in value_dict, but in the attribute_mask (therefore valid)
    will return the default_value passed (usually that is None).

    Internally a list is used to store the values, leaving the keys in the
    Session objects - for many instances this saves a considerable amount
    of memory.

    .. todo:: Make some numbers up to prove this :-)
    '''
    def __init__(self, session, value_dict, default_value=None):
        '''Creates a Song (a set of attributes) that behaves like a dictionary.

        :param session: A Session objective (the session this song belongs to)
        :param value_dict: A mapping from the keys to the values you want to set.
        :param default_value: The value to be returned for valid but unset keys.
        '''
        # Make sure the list is as long as the attribute_mask
        SessionMapping.__init__(self, session, default_value=default_value)
        self._distances = {}

        # Insert the data to the store:
        for key, value in value_dict.items():
            self._store[session.attribute_mask_index_for_key(key)] = value

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

    def distance_add(self, other_song, distance):
        '''Add a relation to ``other_song`` with a certain distance.

        :raises: A **KeyError** if no such key exists.
        '''
        # Make sure that same songs always get 0.0 as distance.
        if hash(self) == hash(other_song):
            distance = 0.0

        self._distances[other_song] = distance
        other_song._distances[self] = distance

    def distance_del(self, other_song):
        '''Delete the relation to ``other_song``

        :raises: A **KeyError** if no such key exists.
        '''
        self._distances.pop(other_song)
        other_song._distances.pop(self)

    def distance_get(self, other_song, default_value=None):
        '''Return the distance to the song ``other_song``

        :param other_song: The song to lookup the relation to.
        :param default_value: The default value to return (default to None)
        :returns: A Distance.
        '''
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

            song_one.distance_add(song_two, 0.7)
            song_one.distance_add(song_one, 421)  # this should be clamped to 1
            self.assertEqual(song_one.distance_get(song_one), 0.0)
            self.assertEqual(song_one.distance_get(song_two), 0.7)

    unittest.main()
