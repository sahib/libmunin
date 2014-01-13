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

# Internal:
from munin.distance import DistanceFunction

# External:
from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance


class LevenshteinDistance(DistanceFunction):
    """Compute the damerau-levenshtein distance of two words.

    **Takes:** two lists of length 1.
    """
    def do_compute(self, lefts, rights):
        lev = normalized_damerau_levenshtein_distance
        dist_sum = 0

        smaller, larger = sorted((lefts, rights), key=len)
        for word_a in larger:
            dist_sum += min(lev(word_b, word_a) for word_b in smaller)

        return dist_sum / len(larger)

if __name__ == '__main__':
    import unittest

    class TestLevenshteinDistance(unittest.TestCase):
        def test_cmp(self):
            dfunc = LevenshteinDistance()
            for i in range(1000000):
                dfunc.do_compute(('berta', ), ('berte', ))

    unittest.main()
