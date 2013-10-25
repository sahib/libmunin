#!/usr/bin/env python
# encoding: utf-8

'''
.. currentmodule:: munin.provider.attic

Overview
--------

The Attic Provider is useful when the caching of a value is desired for memory
efficieny. Instead of saving a potentially often duplicated value seperate
only a ID to a Lookuptable is stored.

Reference
---------
'''

from munin.provider import DirectProvider
from bidict import bidict


class AtticProvider(DirectProvider):
    "Provider that caches it's input arguments"
    def __init__(self):
        '''This provider is useful for data may suffer heavily from duplication.

        Instead from passing it through like :class:`munin.provider.DirectProvider` we'll return
        an index that can be compared directly too for equality.

        If you want to transform the index back to the actual value you
        can use the :func:`lookup` method.

        .. note::

            Input values must be hashable for this to work.
        '''
        DirectProvider.__init__(self, 'Attic')
        self._store = bidict()
        self._last_id = 0

    def process(self, input_value):
        '''Feed a value to the attic.

        :param input_value: A hashable value.
        :returns: An unique index.
        '''
        if input_value in self._store:
            return self._store[input_value]

        self._last_id += 1
        self._store[input_value] = self._last_id
        return self._last_id

    def is_valid_index(self, idx):
        '''Checks if an index is valid.

        .. note:: All indices returned by ``process()`` should be valid.

        :param idx: The index to check.
        :returns: True if valid.
        '''
        return idx > 0 and idx <= self._last_id

    def lookup(self, idx):
        '''Transform the index back to an actual value.

        :param idx: The index to transform.
        '''
        # BiDict backwards mapping syntax:
        return self._store[:idx]


if __name__ == '__main__':
    import unittest

    class AtticTests(unittest.TestCase):
        def test_storage(self):
            provider = AtticProvider()
            self.assertEqual(provider.process('Akrea'), 1)
            self.assertEqual(provider.process('Akrea'), 1)
            self.assertEqual(provider.process('akrea'), 2)

            self.assertEqual(provider.lookup(1), 'Akrea')
            self.assertEqual(provider.lookup(2), 'akrea')

            with self.assertRaises(KeyError):
                self.assertEqual(provider.lookup(3), None)

            self.assertTrue(provider.is_valid_index(1))
            self.assertTrue(provider.is_valid_index(2))
            self.assertTrue(not provider.is_valid_index(0))
            self.assertTrue(not provider.is_valid_index(3))

    unittest.main()
