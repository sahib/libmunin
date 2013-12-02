#!/usr/bin/env python
# encoding: utf-8

'''
Commonly utility functions used througout.
'''

from collections import Mapping, Hashable
from itertools import chain, islice, cycle
import sys


# There does not seem to be a built-in for this.
float_cmp = lambda a, b: abs(a - b) < sys.float_info.epsilon


def sliding_window(iterable, n=2, step=1):
    '''Iterate over an iterable with a sliding window of size `n`.

    This works best if len(iterable) can be cheaply calculated.

    :param iterable: The iterable to provide an iterator for.
    :param n: The size of the window (max size)
    :param step: How much right shall the window be tranformed with each iteration?
    :returns: a generator that yields slices as windows.
    '''
    n2 = n // 2
    for idx in range(0, len(iterable), step):
        fst, snd = idx - n2, idx + n2
        if fst < 0:
            yield chain(iterable[fst:], iterable[:snd])
        else:
            yield islice(iterable, fst, snd)


def centering_window(iterable, n=4, parallel=True):
    '''Provide an iterator that moves windows slowly towards center of the iterable.

    :param iterable: The iterable to provide an iterator for.
    :param parallel: If False the window move together, if True they move parallel to each other.
    :param n: The size of the window.
    :returns: a generator that yields slices as windows.
    '''
    l2 = len(iterable) // 2
    n2 = n // 2

    # Make indexing easier by cutting it in half:
    lean = iterable[:l2]
    mean = iterable[l2:] if parallel else iterable[:(l2 - 1):-1]
    area = range(0, l2, n2)

    # Return an according iterator
    return (chain(lean[idx:idx + n2], mean[idx:idx + n2]) for idx in area)


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))


class SessionMapping(Mapping):
    # Note: Use __slots__ (sys.getsizeof will report even more memory, but # pympler less)
    __slots__ = ('_store', '_session')

    def __init__(self, session, input_dict, default_value=None):
        # Make sure the list is as long as the attribute_mask
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


if __name__ == '__main__':
    import unittest

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

    unittest.main()
