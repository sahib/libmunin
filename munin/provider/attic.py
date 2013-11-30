#!/usr/bin/env python
# encoding: utf-8

'''
.. currentmodule:: munin.provider.attic

Overview
--------

Attic Provider is useful when the caching of a value is desired for memory
efficieny. Instead of saving a potentially often duplicated value seperate
only a ID to a Lookuptable is stored.

**Usage Example:** ::

    >>> p = AtticProvider()
    >>> p.process('Breaking Berta')  # First remember it...
    1
    >>> p.process('Breaking Berta')  # Same!
    1
    >>> p.is_valid_index(2)
    False
    >>> p.process('Game of Loans')   # New values get autoincremented.
    2
    >>> p.is_valid_index(2)
    True
    >>> p.reverse(2)
    'Game of Loans'

As seen above: This Provider is reversable. (``is_reversible`` will yield True)

Reference
---------
'''

from munin.provider import Provider
from bidict import bidict


class AtticProvider(Provider):
    "Provider that caches it's input arguments"
    def __init__(self):
        '''This provider is useful for data may suffer heavily from duplication.

        Instead from passing it through like :class:`munin.provider.Provider` we'll return
        an index that can be compared directly too for equality.

        If you want to transform the index back to the actual value you
        can use the :func:`reverse` method.

        .. note::

            Input values must be hashable for this to work.
        '''
        Provider.__init__(self, 'Attic', is_reversible=True)
        self._store = bidict()
        self._last_id = 0

    def process(self, input_value):
        '''Feed a value to the attic.

        :param input_value: A hashable value.
        :returns: An unique index.
        '''
        if input_value in self._store:
            return (self._store[input_value], )

        self._last_id += 1
        self._store[input_value] = self._last_id
        return (self._last_id, )

    def is_valid_index(self, idx_list_or_scalar):
        '''Checks if an index is valid.

        .. note:: All indices returned by ``process()`` should be valid.

        :param idx_list_or_scalar: The index to check.
        :type idx_list_or_scalar: Either a single int or a list of ints.
        :returns: True if (all are) valid.
        '''
        is_valid = lambda idx: idx > 0 and idx <= self._last_id
        try:
            return all(is_valid(idx) for idx in idx_list_or_scalar)
        except TypeError:
            # Assume it's only one index
            return is_valid(idx_list_or_scalar)

    def reverse(self, idx_list):
        '''Transform the indices back to an actual value.

        :param idx_list: A list of indices to transform.
        '''
        # BiDict backwards mapping syntax:
        return tuple(self._store[:idx] for idx in idx_list)


if __name__ == '__main__':
    import unittest

    class AtticTests(unittest.TestCase):
        def test_storage(self):
            provider = AtticProvider()
            self.assertEqual(provider.process('Akrea'), (1, ))
            self.assertEqual(provider.process('Akrea'), (1, ))
            self.assertEqual(provider.process('akrea'), (2, ))

            self.assertEqual(provider.reverse((1, )), ('Akrea', ))
            self.assertEqual(provider.reverse((2, )), ('akrea', ))

            with self.assertRaises(KeyError):
                self.assertEqual(provider.reverse((3, )), None)

            self.assertTrue(provider.is_valid_index(1))
            self.assertTrue(provider.is_valid_index(2))
            self.assertTrue(not provider.is_valid_index(0))
            self.assertTrue(not provider.is_valid_index(3))

    unittest.main()
