#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Contains method that help the user of the library finding the date he needs.

*Helpers*:

    * :class:`AudioFileWalker` - generator class that yields files to audio files.
    * :func:`song_or_uid` - function that delivers the song for uids or just
                            returns the song if passed in.

    * :func:`pairup` - Easy Mask building.

Reference
---------
"""

from collections import Mapping
from itertools import chain, islice, zip_longest

import math
import sys
import os


###########################################################################
#                             AudioFileWalker                             #
###########################################################################


ALLOWED_FORMATS = ['mpc', 'mp4', 'mp3', 'flac', 'wav', 'ogg', 'm4a', 'wma']


class AudioFileWalker:
    """File Iterator that yields all files with a specific ending.
    """
    def __init__(self, base_path, extensions=ALLOWED_FORMATS):
        """There ist a list of default extensions in
        ``munin.helpers.ALLOWED_FORMATS`` with the most common formats.

        This class implements ``__iter__``, so you just can start using it.

        :param base_path: Recursively seach files in this path.
        :param extensions: An iterable of extensions that are allowed.
        """
        self._base_path = base_path
        self._extension = set(extensions)

    def __iter__(self):
        for root, _, files in os.walk(self._base_path):
            for path in files:
                ending = path.split('.')[-1]
                if ending in self._extension:
                    yield os.path.join(root, path)


###########################################################################
#                               Misc Utils                                #
###########################################################################

def song_or_uid(database, song_or_uid):
    """Takes a song or the uid of it and return the song.

    This function is purely for your convinience,
    you can always use :func:`munin.database.Database.__getitem__`

    :param database: Database to lookup uid from.
    :raises: IndexError on invalid uid.
    :returns: A :class:`munin.song.Song` in any case.
    """
    if hasattr(song_or_uid, 'uid'):
        return song_or_uid
    return database[song_or_uid]


def pairup(provider, distance_function, weight):
    """Convienience function for easy mask building.

    Every distance function needs to know the provider that processed the value.
    This is needed to implement the compress functionality. In order to stop you
    from writing code like this:

        >>> prov = Provider()
        >>> dfunc = DistanceFunction(prov)
        >>> # Somehwere down:
        >>> {'artist': (prov, dfunc, 0.5)}

    You can just write:

        >>> {'artist': pairup(Provider(), DistanceFunction(), 0.5)}

    This function will set the provider in the DistanceFunction for you.
    """
    if distance_function is not None:
        distance_function._provider = provider
    return (provider, distance_function, weight)


###########################################################################
#                              Numeric Utils                              #
###########################################################################


# There does not seem to be a built-in for this.
float_cmp = lambda a, b: abs(a - b) < sys.float_info.epsilon


###########################################################################
#                         Very special Iterators                          #
###########################################################################


def sliding_window(iterable, n=2, step=1):
    """Iterate over an iterable with a sliding window of size `n`.

    This works best if len(iterable) can be cheaply calculated.

    :param iterable: The iterable to provide an iterator for.
    :param n: The size of the window (max size)
    :param step: How much right shall the window be tranformed with each iteration?
    :returns: a generator that yields slices as windows.
    """
    n2 = n // 2
    for idx in range(0, len(iterable), step):
        fst, snd = idx - n2, idx + n2
        if fst < 0:
            yield chain(iterable[fst:], iterable[:snd])
        else:
            yield islice(iterable, fst, snd)


def centering_window(iterable, n=4, parallel=True):
    """Provide an iterator that moves windows slowly towards center of the iterable.

    :param iterable: The iterable to provide an iterator for.
    :param parallel: If False the window move together, if True they move parallel to each other.
    :param n: The size of the window.
    :returns: a generator that yields slices as windows.
    """
    l2 = len(iterable) // 2
    n2 = n // 2

    # Make indexing easier by cutting it in half:
    lean = iterable[:l2]
    mean = iterable[l2:] if parallel else iterable[:(l2 - 1):-1]
    area = range(0, l2, n2)

    # Return an according iterator
    return (chain(lean[idx:idx + n2], mean[idx:idx + n2]) for idx in area)


###########################################################################
#                           Itertools Recipes:                            #
###########################################################################


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


class RunningMean:
    def __init__(self):
        self.mean = self.rsdv = 0.0
        self.samples = 1

    def add(self, value):
        last_diff = value - self.mean
        self.mean += last_diff / self.samples
        self.rsdv += last_diff * (value - self.mean)
        self.samples += 1

    @property
    def sd(self):
        if self.samples <= 2:
            return 0.0

        v = math.sqrt(self.rsdv / (self.samples - 2))
        return v

###########################################################################
#                             SessionMapping                              #
###########################################################################


class SessionMapping(Mapping):
    # Note: Use __slots__ (sys.getsizeof will report even more memory, but # pympler less)
    __slots__ = ('_store', '_session')

    def __init__(self, session, input_dict, default_value=None):
        # Make sure the list is as long as the mask
        self._store = [default_value] * session.mask_length
        self._session = session

        # Insert the data to the store:
        for key, value in input_dict.items():
            self._store[session.index_for_key(key)] = value

    ####################################
    #  Mapping Protocol Satisfication  #
    ####################################

    def __getitem__(self, key):
        return self._store[self._session.index_for_key(key)]

    def __iter__(self):
        def _iterator():
            for idx, elem in enumerate(self._store):
                if elem is not None:
                    yield self._session.key_at_index(idx), elem
        return _iterator()

    def __len__(self):
        return self._session.mask_length

    def __contains__(self, key):
        return key in self.keys()

    ###############################################
    #  Making the utility methods work correctly  #
    ###############################################

    def values(self):
        return iter(self._store)

    def keys(self):
        at = self._session.key_at_index
        return (at(idx) for idx, v in enumerate(self._store) if v is not None)

    def items(self):
        return iter(self)

###########################################################################
#                              Stupid Tests                               #
###########################################################################


if __name__ == '__main__':
    import unittest

    if not '--cli' in sys.argv:
        class TestUtils(unittest.TestCase):
            def test_sliding_window(self):
                wnds = list(sliding_window([1, 2, 3, 4], 2, 2))
                a, b = wnds
                self.assertEqual(list(a), [4, 1])
                self.assertEqual(list(b), [2, 3])

            def test_centering_window(self):
                wnds = list(centering_window(range(10), 4, parallel=False))
                wnds = [list(w) for w in wnds]
                ex = [[0, 1, 9, 8], [2, 3, 7, 6], [4, 5]]
                self.assertEqual(ex, wnds)

            def test_running_mean(self):
                run = RunningMean()
                self.assertAlmostEqual(run.mean, 0.0)
                self.assertAlmostEqual(run.sd, 0.0)
                run.add(1)
                run.add(2)
                run.add(3)
                self.assertAlmostEqual(run.mean, 2.0)
                self.assertAlmostEqual(run.sd, 1.0)

        unittest.main()
    else:
        walker = AudioFileWalker(sys.argv[1])
        for path in walker:
            print(path)
