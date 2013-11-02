#!/usr/bin/env python
# encoding: utf-8

'''
Commonly utility functions used througout.
'''

from collections import Mapping, Hashable
import sys


# There does not seem to be a built-in for this.
float_cmp = lambda a, b: abs(a - b) < sys.float_info.epsilon


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
        return (at(idx) for idx in range(len(self._store)))

    def items(self):
        return iter(self)
