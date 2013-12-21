#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Compute the distance of two keywordsetlists using the Average-Linkage:

    http://en.wikipedia.org/wiki/Hierarchical_clustering#Linkage_criteria

This can be used with:

    * :class:`munin.provider.KeywordsProvider`

Reference
---------
"""

# Stdlib:
from itertools import product

# Internal:
from munin.distance import DistanceFunction
from munin.helper import float_cmp


class KeywordsDistance(DistanceFunction):
    """
    The distance between two keywords is computes as follows:

        :math:`distance(A, B) = \\min(\\frac{\\vert a\\cup b\\vert}{\\max \\vert a \\vert, \\vert b \\vert} \\forall a, b \\in A \\times B)`

    where *A* and *B* are the list of keywords to compare, and *a* and *b* are
    the individual keywordsets.
    """
    def do_compute(self, lefts, rights):
        if not lefts or not rights:
            return 1.0

        old_distance = 1.0
        for kwa, kwb in product(lefts, rights):
            union = kwa & kwb
            if not union:
                continue

            distance = 1.0 - len(union) / max(len(kwa), len(kwb))
            old_distance = min(old_distance, distance)
            if float_cmp(distance, 0.0):
                break

        return old_distance


if __name__ == '__main__':
    import unittest

    class TestKeywordsDistance(unittest.TestCase):
        def test_basic(self):
            dist = KeywordsDistance()
            self.assertAlmostEqual(dist.do_compute(
                [frozenset(['a', 'b']), frozenset(['c', 'd'])],
                [frozenset(['a', 'c']), frozenset(['b', 'd'])]
            ), 0.5)
            self.assertAlmostEqual(dist.do_compute(
                [frozenset(['a', 'b']), frozenset(['c', 'd'])],
                [frozenset(['a', 'x']), frozenset(['y', 'd'])]
            ), 0.5)
            self.assertAlmostEqual(dist.do_compute(
                [frozenset(['a', 'b']), frozenset(['c', 'd'])],
                [frozenset(['a', 'b']), frozenset(['c', 'd'])]
            ), 0.0)
            self.assertAlmostEqual(dist.do_compute(
                [frozenset(['a', 'b']), frozenset(['c', 'd'])],
                [frozenset(['x', 'y']), frozenset(['z', 'ö'])],
            ), 1.0)

            # self.assertTrue(False)

    unittest.main()
