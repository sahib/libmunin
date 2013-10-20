#!/usr/bin/env python
# encoding: utf-8

from munin.caching import get_cache_path, check_or_mkdir

from collections import Mapping
from shutil import rmtree
from copy import copy


class Song(Mapping):
    '''A song is a readonly mapping of keys to values (like a readonly dict).

    The keys will depend on the attribute mask in the session.
    The values will be passed as value_dict to the constructor.
    Keys that are no in value_dict, but in the attribute_mask (therefore valid)
    will return the default_value passed (usually that is None).

    Internally a list is used to store the values, leaving the keys in the
    Session objects - for many instances this saves a considerable amount
    of memory. (TODO: Make some numbers [up])
    '''
    def __init__(self, session, value_dict, default_value=None):
        '''Creates a Song (a set of attributes) that behaves like a dictionary.

        :param session: A Session object (the session this song belongs to)
        :param value_dict: A mapping from the keys to the values you want to set.
        :param default_value: The value to be returned for valid but unset keys.
        '''
        # Make sure the list is as long as the attribute_mask
        self._store = [default_value] * session.attribute_mask_len
        self._session = session

        # Insert the data to the store:
        for key, value in value_dict.items():
            self._store[session.attribute_mask_index_for_key(key)] = value

    ####################################
    #  Mapping Protocol Satisfication  #
    ####################################

    def __getitem__(self, key):
        return self._store[self._session.attribute_mask_index_for_key(key)]

    def __iter__(self):
        def _iterator():
            for idx, elem in enumerate(self._store):
                yield self._session.attribute_mask_key_at_index(idx), elem
        return _iterator()

    def __len__(self):
        return len(self._session.attribute_mask_len)

    def __contains__(self, key):
        return key in self.keys()

    ###############################################
    #  Making the utility methods work correctly  #
    ###############################################

    def values(self):
        return iter(self._store)

    def keys(self):
        # I've had a little too much haskell in my life:
        at = self._session.attribute_mask_key_at_index
        return (at(idx) for idx in range(len(self._store)))

    def items(self):
        return iter(self)

    #################################
    #  Additional helper functions  #
    #################################

    def to_dict(self):
        'Shortcut for dict(iter(song))'
        return dict(iter(song))


class Session:
    def __init__(self, name, attribute_mask):
        self._attribute_mask = copy(attribute_mask)
        self._attribute_list = list(attribute_mask)
        self._listidx_to_key = {k: i for i, k in enumerate(self._attribute_list)}

    # Make this only gettable, so we can distribute the reference
    # around all session objects.
    @property
    def attribute_mask(self):
        return copy(self._attribute_mask)

    @property
    def attribute_mask_len(self):
        return len(self._attribute_mask)

    def attribute_mask_key_at_index(self, idx):
        return self._attribute_list[idx]

    def attribute_mask_index_for_key(self, key):
        return self._listidx_to_key[key]

    @staticmethod
    def load_from(session_name):
        base = get_cache_path(session_name)
        os.path.join()
        return Session(session_name, {})

    def save_to(self, name):
        base = get_cache_path(name)
        if os.path.exists(path):
            rmtree(base)
        check_or_mkdir(base)


if __name__ == '__main__':
    import unittest

    class SongTests(unittest.TestCase):
        def setUp(self):
            self._session = Session('test', {
                'genre': None,
                'artist': None
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

    unittest.main()
