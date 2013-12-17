#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from itertools import product

# Internal:
from munin.distance import DistanceFunction
from munin.helper import float_cmp

# External:
from pyxdameraulevenshtein import damerau_levenshtein_distance


class LevenshteinDistance(DistanceFunction):
    def do_compute(self, lefts, rights):
        min_dist = 1.0
        for left, right in product(lefts, rights):
            max_both = max(len(left), len(right))
            if max_both is 0:
                continue

            new_dist = damerau_levenshtein_distance(left, right) / max_both
            min_dist = min(min_dist, new_dist)

            # Optimization: Often we get a low value early.
            if float_cmp(min_dist, 0.0):
                break

        return min_dist

if __name__ == '__main__':
    import unittest

    class TestLevenshteinDistance(unittest.TestCase):
        def test_cmp(self):
            dfunc = LevenshteinDistance()
            for i in range(1000000):
                dfunc.do_compute(('berta', ), ('berte', ))

    unittest.main()
