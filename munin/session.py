#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

:class:`Session` is the main entrance to using libmunin.

It implements a caching layer around the lower level API, being able to
save a usage-*Session* for later re-use. The session data will be saved packed
on disk as a .gzip archive.

Apart from this it holds the **Attribute Mask** - in simple words:
the part where you tell libmunin what data you have to offer and how
you want to configure the processing of it.

Reference
---------
"""

# Standard:
from shutil import rmtree
from copy import copy
from contextlib import contextmanager

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

from bidict import bidict


# Internal:
from munin.database import Database
from munin.helper import song_or_uid
import munin.graph


def check_or_mkdir(path):
    'Check if path does exist, if not mkdir it.'
    if not os.path.exists(path):
        os.mkdir(path)


def get_cache_path(extra_name=None):
    """Tries to find out the XDG caching path of your system.

    This is done preferrably with PyXDG. If it's not installed,
    we try the XDG_CACHE_HOME environment variable or default to ~/.cache/

    If the path does not exist yet it will be created for you.

    :param extra_name: Extra path component to append to the path (or None).
    :returns: The full path, e.g.: /home/user/.cache/libmunin/<extra_name>
    """
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
    'max_neighbors': 5,
    'max_distance': 0.999,
}


DefaultConfig = type('DefaultConfig', (), dict(DEFAULT_CONFIG, __doc__="""
Example: ::

    >>> from munin.session import DefaultConfig as default
    >>> default.max_neighbors
    100

Alternatively without :class:`DefautltConfig`: ::

    >>> from munin.session import DEFAULT_CONFIG
    >>> DEFAULT_CONFIG['max_neighbors']
    100

The sole purpose of this class is to save a bit of typing.


.. note::

    It is possible to mutate the DEFAULT_CONFIG dict to have the same defaults
    for every session.
"""
))


class Session:
    """Main API to *libmunin* and caching layer."""
    def __init__(self, name, mask, config=None):
        """Create a new session:

        :param name: The name of the session. Used to load it again from disk.
        :param mask: The attribute mask. See :term:`Mask`
        :param config: A dictionary with config values. See :class:`DefaultConfig` for available keys.
        """
        self._config = config or DEFAULT_CONFIG
        self._name = name

        # Make access to the attribute mask more efficient
        self._mask = copy(mask)
        self._attribute_list = sorted(mask)
        self._listidx_to_key = {k: i for i, k in enumerate(self._attribute_list)}

        # Lookup tables for those attributes (fast access is crucial here)
        def make_index(idx, default_func):
            index = {}
            for key, descr in self._mask.items():
                if descr[idx] is not None:
                    index[key] = descr[idx]
                else:
                    index[key] = default_func(key)

            return index

        # Import this locally, since we might get circular import otherway:
        from munin.distance import DistanceFunction
        from munin.provider import Provider

        # Build indices and set default values:
        self._key_to_providers = make_index(0,
                lambda key: Provider()
        )
        self._key_to_distfuncs = make_index(1,
                lambda key: DistanceFunction(self._key_to_providers[key])
        )
        self._key_to_weighting = make_index(2,
                lambda key: 1.0
        )

        # Sum of the individual weights, pre-calculated once.
        self._weight_sum = sum((descr[2] for descr in mask.values()))

        # Create the associated database.
        self._database = Database(self)

        # Publicly readable attribute.
        self.mapping = bidict()

    def __getitem__(self, idx):
        return self.database[idx]

    @property
    def name(self):
        'Return the name you passed to the session'
        return self._name

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
    def mask(self):
        'Returns a copy of the attribute mask (as passed in)'
        return copy(self._mask)

    @property
    def mask_length(self):
        'Returns the length of the attribte mask (number of keys)'
        return len(self._mask)

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
        return self._key_to_distfuncs[key]

    def weight_for_key(self, key):
        'Get the weighting (*float*) for ``key``'
        return self._key_to_weighting[key]

    def _weight(self, dist_dict):
        'This is in Session for performance reasons'
        dist_sum = 0.0

        for key, (_, _, weight) in self._mask.items():
            try:
                dist_sum += dist_dict[key] * weight
            except KeyError:
                dist_sum += weight

        return dist_sum / self._weight_sum

    ############################
    #  Caching Implementation  #
    ############################

    @staticmethod
    def from_archive_path(full_path):
        """Load a cached session from a file on the disk.

        Example usage: ::

            >>> Session.from_archive_path('/tmp/test.gz')
            <Session object at 0x2343424>

        .. note::

            If you prefer to save the sessions in XDG_CACHE_HOME anyway,
            just use :func:`Session.from_name`.

        :param full_path: a path to a packed session.
        :type full_path: str
        :returns: A cached session.
        :rtype: :class:`Session`
        """
        base_path, _ = os.path.splitext(full_path)
        with tarfile.open(full_path, 'r:*') as tar:
            tar.extractall(base_path)

        with open(os.path.join(base_path, 'session.pickle'), 'rb') as handle:
            return pickle.load(handle)

    @staticmethod
    def from_name(session_name):
        """Like :func:`from_archive_path`, but be clever and load it
        from *${XDG_CACHE_HOME}/libmunin/<session_name>/session.pickle*

        :param session_name: The name of a session.
        :type session_name: str
        :returns: A cached session.
        :rtype: :class:`Session`
        """
        return Session.from_archive_path(get_cache_path(session_name))

    def save(self, path=None, compress=True):
        """Save the session (and all caches) to disk.

        :param path: Where to save the session in. If none XDG_CACHE_HOME is used.
        :param compress: Compress the resulting folder with **gzip**?
        """
        path = os.path.join(path, self.name) if path else get_cache_path(self.name)
        if os.path.isfile(path):
            os.remove(path)
        if os.path.isdir(path):
            rmtree(path, ignore_errors=True)
        os.mkdir(path)

        with open(os.path.join(path, 'session.pickle'), 'wb') as handle:
            pickle.dump(self, handle)

        with tarfile.open(path + '.gz', 'w:gz') as tar:
            tar.add(path, arcname='')

        shutil.rmtree(path)

    ###########################################################################
    #                             Recommendations                             #
    ###########################################################################

    def recommend_from_attributes(self, subset, number=20):
        """Find n recommendations solely from intelligent guessing.

        This will try to find a good rule, that indicates a user's
        favourite song, and will call :func:`recommendations_from_seed` on it.
        If no rules are known, the most played song will be chosen.
        If there is none, a random song is picked.

        The first song in the recommendations yielded is the seed song.

        .. seealso: :func:`recommendations_from_seed`
        """
        return munin.graph.recommendations_from_attributes(
            subset,
            self.database,
            self.database.rule_index,
            number
        )

    def recommend_from_seed(self, song, number=20):
        """Recommend songs based on a certain attribute.

        For example you can search by a certain genre by calling it like this: ::

            >>> recommend_from_attributes({'genre', 'death metal'}, ...)

        The value passed must match fully, no fuzzy matching is performed.

        :returns: Recommendations like the others or None if no suitable song found.
        """
        song = song_or_uid(self.database, song)
        return munin.graph.recommendations_from_seed(
            self.database,
            self.rule_index,
            song,
            number
        )

    def recommend_from_heuristic(self, number=20):
        """Give 'n' recommendations based on 'song'.

        - Will lookup rules for song.
        - If no rules found, a breadth first search starting with song is performed.
        - Otherwise, breadth first from songs mentioned in the rules are done.

        The first song in the recommendations yielded is the seed song.

        :param graph: The graph to breadth first search on.
        :type graph: :class:`igraph.Graph`
        :param rule_index: Rule database.
        :type rule_index: :class:`munin.history.RuleIndex`
        :param song: Song to base recommendations on.
        :type song: :class:`munin.song.Song`
        :param n: Deliver so many recommendations (at max.)
        :returns: An iterator that yields recommend songs.
        """
        return munin.graph.recommendations_from_graph(
            self.database,
            self.rule_index,
            number
        )

    def explain_recommendation(self, seed_song, recommendation, max_reasons=3):
        """Explain the recommendation you got.

        **Usage Example:**

            >>> explain_recommendation(seed_song, recommendation)
            (~0.4, [
                ('genre', 0.1),    # Very similar common attribute
                ('moodbar', 0.2),  # Quite similar
                ('lyrics', 0.5)    # Well, that's okay.
            ])

        :param seed_song: The seed song used.
                          For ``_heuristic`` and ``_attribute`` this is the first song.
        :param recommendation: The recommendation you want to have explained.
        :param max_reasons: How many reasons to yield at a maximum.
        :retruns: Tuple of the total distance to each other and a list of pairs
                  that consist of (attribute_name: subdistance_float)
        """
        return munin.graph.explain_recommendation(
            seed_song,
            recommendation,
            max_reasons
        )

    ###########################################################################
    #                          Proxy Methods                                  #
    ###########################################################################

    def feed_history(self, song):
        """Feed a single song to the history.

        If the feeded song is not yet in the database,
        it will be added automatically.

        :param song: The song to feed in the history.
        """
        self.database.feed_history(song)

    def add(self, value_mapping):
        """Add a song with the values in the ``value_mapping``.

        This function should be always called like this to trigger a rebuild:

        .. code-block:: python

            >>> with session.transaction():
            ...     session.add({'genre': 'death metal', ...})

        :param dict value_mapping: A mapping :term:`Attribute` : Value.
        :raises KeyError: If an unknown :term:`Attribute` was used.
        :returns: The *UID* of the newly added song.
        """
        return self.database.add(value_mapping)

    def insert(self, value_mapping):
        """Insert a song without triggering a rebuild.

        This function should be always called like this to trigger a cleanup of the graph:

        .. code-block:: python

            >>> with session.transaction():
            ...     session.add({'genre': 'death metal', ...})

        The rest is the same as with :meth:`add`.
        """
        return self.database.insert(value_mapping)

    def remove(self, song):
        """Remove a single song (or *UID*) from the Graph.

        This function will try to close the hole. If :meth:`insert`
        is called afterwards the *UID* of the deleted song will be re-used.

        :returns: The *UID* of the deleted song.
        """
        song = song_or_uid(self.database, song)
        return self.database.remove(song.uid)

    def playcount(self, song):
        """Get the playcount of a song.

        If no playcount is known for it, 0 will be returned.

        :returns: Number of times this song was played.
        :rtype: int
        """
        return self.database.playcount(song)

    def playcounts(self, n=0):
        """Get all playcounts, or the most common.

        :param n: The number of most  common plays to select. Might be less.
        :returns: A list of tuples if n > 0, or a Mapping.
        """
        return self.database.playcounts(n)

    def find_matching_attributes(self, subset):
        """Search the database for a subset of the attributes/values in subset.

        Example: ::

            >>> find_matching_attributes({'genre': 'metal', 'artist': 'Debauchery'})

        :returns: A lazy iterator over the matching songs.
        """
        return self.database.find_matching_attributes(subset)

    @contextmanager
    def transaction(self):
        'Convienience method: Excecute block and call :func:`rebuild` afterwards.'
        with self.fix_graph():
            try:
                yield
            finally:
                self.database.rebuild()

    @contextmanager
    def fix_graph(self):
        """Fix the previosuly rebuild graph.

        This means checking if unsorted distances can be found (which should not happend)
        and checking if unidirectional edges can be found (which get deleted).

        You should this contextmanager when calling :meth:`insert` or :meth:`remove`.
        """
        try:
            yield
        finally:
            self.database.fix_graph()

    @property
    def rule_index(self):
        return self.database._rule_index

    @property
    def listen_history(self):
        return self.database._listen_history


if __name__ == '__main__':
    import unittest

    class SessionTests(unittest.TestCase):
        def setUp(self):
            self._session = Session('session_test', {
                'genre': (None, None, 0.2),
                'artist': (None, None, 0.3)
            })

        def test_writeout(self):
            self._session.save('/tmp')
            path = '/tmp/session_test.gz'
            self.assertTrue(os.path.isfile(path))
            new_session = Session.from_archive_path(path)
            self.assertTrue(os.path.isdir(path[:-3]))
            self.assertEqual(
                    new_session.mask,
                    {'genre': (None, None, 0.2), 'artist': (None, None, 0.3)}
            )

        # TODO: This needs more testing.

    unittest.main()
