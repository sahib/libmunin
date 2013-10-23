#!/usr/bin/env python
# encoding: utf-8

from collections import Mapping
from shutil import rmtree
from copy import copy

import tarfile
import shutil
import pickle
import os

try:
    from xdg import BaseDirectory
    HAS_XDG = True
except ImportError:
    HAS_XDG = False


def check_or_mkdir(path):
    'Check if path does exist, if not mkdir it.'
    if not os.path.exists(path):
        os.mkdir(path)


def get_cache_path(extra_name=None):
    '''Tries to find out the XDG caching path of your system.

    This is done preferrably with PyXDG. If it's not installed,
    we try the XDG_CACHE_HOME environment variable or default to ~/.cache/

    If the path does not exist yet it will be created for you.

    :param extra_name: Extra path component to append to the path (or None).
    :returns: The full path, e.g.: /home/user/.cache/libmunin/<extra_name>
    '''
    if HAS_XDG and 0:
        base_dir = BaseDirectory.xdg_cache_home
    else:
        base_dir = os.environ.get('XDG_CACHE_HOME')
        if base_dir is None:
            base_dir = os.path.join(os.path.expanduser('~'), '.cache')

    base_dir = os.path.join(base_dir, 'libmunin')
    check_or_mkdir(base_dir)
    return base_dir if not extra_name else os.path.join(base_dir, extra_name)


class Song(Mapping):
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
        'Shortcut for ``dict(iter(song))``'
        return dict(iter(song))


class Session:
    def __init__(self, name, attribute_mask, path=None):
        # Make access to the attribute mask more efficient
        self._attribute_mask = copy(attribute_mask)
        self._attribute_list = list(attribute_mask)
        self._listidx_to_key = {k: i for i, k in enumerate(self._attribute_list)}
        self._path = os.path.join(path, name) if path else get_cache_path(name)

        self._create_file_structure(self._path)

    def _create_file_structure(self, path):
        if os.path.isfile(path):
            os.remove(path)
        if os.path.isdir(path):
            rmtree(path, ignore_errors=True)

        os.mkdir(path)
        for subdir in ['distances', 'providers', 'rules']:
            os.mkdir(os.path.join(path, subdir))

    def _compress_directory(self, path, remove=True):
        with tarfile.open(path + '.gz', 'w:gz') as tar:
            tar.add(path, arcname='')

        if remove is True:
            shutil.rmtree(path)

    ###############################
    #  Attribute Mask Attributes  #
    ###############################

    # Make this only gettable, so we can distribute the reference
    # around all session objects.
    @property
    def attribute_mask(self):
        'Returns a copy of the attribute mask (as passed in)'
        return copy(self._attribute_mask)

    @property
    def attribute_mask_len(self):
        'Returns the length of the attribte mask (number of keys)'
        return len(self._attribute_mask)

    def attribute_mask_key_at_index(self, idx):
        'Retrieve the key of the attribute mask at index ``idx``'
        return self._attribute_list[idx]

    def attribute_mask_index_for_key(self, key):
        'Retrieve the index for the key given by ``key``'
        return self._listidx_to_key[key]

    ############################
    #  Caching Implementation  #
    ############################

    @staticmethod
    def from_archive_path(full_path, name=None):
        base_path, _ = os.path.splitext(full_path)
        with tarfile.open(full_path, 'r:*') as tar:
            tar.extractall(base_path)

        with open(os.path.join(base_path, 'mask.pickle'), 'rb') as file_handle:
            mask = pickle.load(file_handle)

        name = name or os.path.basename(base_path)
        return Session(name, mask, path=base_path)

    @staticmethod
    def from_name(session_name):
        return Session.from_archive_path(
                get_cache_path(session_path),
                name=session_path
        )

    def save(self, compress=True):
        '''Save the session (and all caches) to disk.
        '''
        with open(os.path.join(self._path, 'mask.pickle'), 'wb') as handle:
            pickle.dump(self._attribute_mask, handle)

        self._compress_directory(self._path)


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

    class SessionTests(unittest.TestCase):
        def setUp(self):
            self._session = Session('session_test', {
                'genre': None,
                'artist': None
            }, path='/tmp')

        def test_writeout(self):
            self._session.save()
            path = '/tmp/session_test.gz'
            self.assertTrue(os.path.isfile(path))
            new_session = Session.from_archive_path(path)
            self.assertTrue(os.path.isdir(path[:-3]))
            self.assertEqual(
                    new_session.attribute_mask,
                    {'genre': None, 'artist': None}
            )

        # TODO: This needs more testing.

    unittest.main()
