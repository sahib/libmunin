#!/usr/bin/env python
# encoding: utf-8

'''
.. currentmodule:: munin.session

:class:`Session` is the main entrance to using libmunin.
It implements a caching layer around the lower level API, being able to
save a usage-*Session* for later re-use. The session data will be saved packed
on disk as a .gzip archive.

Apart from this it holds the **Attribute Mask** - in simple words:
the part where you tell libmunin what data you have to offer and how
you want to configure the processing of it.
'''

# Standard:
from shutil import rmtree
from copy import copy

import tarfile
import shutil
import pickle
import os

# External:
try:
    from xdg import BaseDirectory
    HAS_XDG = True
except ImportError:
    HAS_XDG = False

# Internal:
from munin.distance import DistanceFunction
from munin.provider import DirectProvider
from munin.database import Database


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


DEFAULT_CONFIG = {
    'max_neighbors': 100,
    'max_distance': 0.999
}


DefaultConfig = type('DefaultConfig', (), DEFAULT_CONFIG)
DefaultConfig.__doc__ = '''
Example: ::

    >>> from munin.session import DefaultConfig as default
    >>> default.max_neighbors
    100

Alternatively without :class:`DefautltConfig`: ::

    >>> from munin.session import DEFAULT_CONFIG
    >>> DEFAULT_CONFIG['max_neighbors']
    100

The sole purpose of this class is to save a bit of typing.
'''


class Session:
    '''Main API to *libmunin* and caching layer.'''
    def __init__(self, name, attribute_mask, path=None, config=None):
        '''Create a new session:

        :param name: The name of the session. Used to load it again from disk.
        :param attribute_mask: The attribute mask. See: TODO
        :param path: The directory to store the sessions in. If none XDG_CACHE_HOME is used.
        :param config: A dictionary with config values. See :class`DEFAULT_CONFIG` for available keys.
        '''
        self._config = config
        self._path = os.path.join(path, name) if path else get_cache_path(name)

        # Make access to the attribute mask more efficient
        self._attribute_mask = copy(attribute_mask)
        self._attribute_list = sorted(attribute_mask)
        self._listidx_to_key = {k: i for i, k in enumerate(self._attribute_list)}

        # Lookup tables for those attributes (fast access is crucial here)
        self._key_to_providers = {}
        self._key_to_dmeasures = {}
        self._key_to_weighting = {}

        for key, descr in self._attribute_mask.items():
            provider, distance_measure, weight = descr

            # Use the default provider:
            if provider is None:
                provider = DirectProvider()

            # Use the standard __eq__ as default:
            if distance_measure is None:
                distance_measure = DistanceFunction(provider)

            # buildup the indices:
            self._key_to_providers[key] = provider
            self._key_to_dmeasures[key] = distance_measure
            self._key_to_weighting[key] = weight

        self._create_file_structure(self._path)

        # Create the associated database.
        self._database = Database(self)

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

    @property
    def database(self):
        'yield the associated :class:`munin.database.Database`'
        return self._database

    @property
    def config(self):
        'Return the config dictionary passed to ``__init__``'
        return self._config

    @property
    def config_class(self):
        'Like DefaultConfig, yield a class that has config keys as attributes.'
        return type('CurrentConfig', (), self._config)

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
    def mask_length(self):
        'Returns the length of the attribte mask (number of keys)'
        return len(self._attribute_mask)

    def key_at_index(self, idx):
        'Retrieve the key of the attribute mask at index ``idx``'
        return self._attribute_list[idx]

    def index_for_key(self, key):
        'Retrieve the index for the key given by ``key``'
        return self._listidx_to_key[key]

    def provider_for_key(self, key):
        'Get the provider for the key in ``key``'
        return self._key_to_providers[key]

    def distance_function_for_key(self, key):
        'Get the :class:`munin.distance.DistanceFunction` for ``key``'
        return self._key_to_dmeasures[key]

    def weight_for_key(self, key):
        'Get the weighting (*float*) for ``key``'
        return self._key_to_weighting[key]

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

        :param compress: Compress the resulting folder with **gzip**?
        '''
        with open(os.path.join(self._path, 'mask.pickle'), 'wb') as handle:
            pickle.dump(self._attribute_mask, handle)

        self._compress_directory(self._path)


if __name__ == '__main__':
    import unittest

    class SessionTests(unittest.TestCase):
        def setUp(self):
            self._session = Session('session_test', {
                'genre': (None, None, 0.2),
                'artist': (None, None, 0.3)
            }, path='/tmp')

        def test_writeout(self):
            self._session.save()
            path = '/tmp/session_test.gz'
            self.assertTrue(os.path.isfile(path))
            new_session = Session.from_archive_path(path)
            self.assertTrue(os.path.isdir(path[:-3]))
            self.assertEqual(
                    new_session.attribute_mask,
                    {'genre': (None, None, 0.2), 'artist': (None, None, 0.3)}
            )

        # TODO: This needs more testing.

    unittest.main()
