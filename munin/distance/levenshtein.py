#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Distance Function that is able to compare two strings using the
Damerau-Levenshtein-Distance.

For computation the ``pyxdameraulevenshtein`` module is used, which is
implemented in Cython.

Reference
---------
"""

# Stdlib:
from itertools import product

# Internal:
from munin.distance import DistanceFunction
from munin.helper import float_cmp

# External:
from pyxdameraulevenshtein import damerau_levenshtein_distance


class LevenshteinDistance(DistanceFunction):
    """Compute the damerau-levenshtein distance of two words.

    **Takes:** two lists of length 1.
    """
    def do_compute(self, lefts, rights):
        left, right = lefts[0], rights[0]
        max_both = max(len(left), len(right))
        return damerau_levenshtein_distance(left, right) / max_both

if __name__ == '__main__':
    import unittest

    class TestLevenshteinDistance(unittest.TestCase):
        def test_cmp(self):
            dfunc = LevenshteinDistance()
            for i in range(1000000):
                dfunc.do_compute(('berta', ), ('berte', ))

    unittest.main()
