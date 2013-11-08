#!/usr/bin/env python
# encoding: utf-8

'''
Commonly utility functions used througout.
'''

from collections import Mapping, Hashable
from itertools import chain, islice
import sys


# There does not seem to be a built-in for this.
float_cmp = lambda a, b: abs(a - b) < sys.float_info.epsilon


def sliding_window(iterable, n=2, step=1):
    n2 = n // 2
    for idx in range(0, len(iterable), step):
        fst, snd = idx - n2, idx + n2
        if fst < 0:
            yield chain(iterable[fst:], iterable[:snd])
        else:
            yield islice(iterable, fst, snd)


def centering_window(iterable, n=1):
    ln = len(iterable)
    for idx in range(0, ln // 2, n):
        fst, snd = idx + n, ln - idx - n
        yield chain(iterable[idx:fst], iterable[snd:snd + n])


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
        return len(self._session.mask_length)

    def __contains__(self, key):
        return key in self.keys()

    ###############################################
    #  Making the utility methods work correctly  #
    ###############################################

    def values(self):
        return iter(self._store)

    def keys(self):
        # I've had a little too much haskell in my life:
        at = self._session.key_at_index
        return filter(None, (at(idx) for idx in range(len(self._store))))

    def items(self):
        return iter(self)


if __name__ == '__main__':
    import unittest

    class TestUtils(unittest.TestCase):
        def test_sliding_window(self):
            for window in sliding_window([1, 2, 3, 4], 2, 2):
                print('//', list(window))

        def test_centering_window(self):
            for window in centering_window(range(16), 2):
                print('==', list(window))

    unittest.main()
