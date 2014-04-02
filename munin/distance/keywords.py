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
from itertools import product, takewhile

# Internal:
from munin.distance import DistanceFunction
from munin.helper import float_cmp


class KeywordsDistance(DistanceFunction):
    """
    The distance between two keywords is computes as follows:

        :math:`distance(A, B) = \\min(\\frac{\\vert a\\cup b\\vert}{\\max \\vert a \\vert, \\vert b \\vert} \\forall a, b \\in A \\times B)`

    *edit*: Nope. Changed.

    where *A* and *B* are the list of keywords to compare, and *a* and *b* are
    the individual keywordsets.
    """
    def do_compute(self, lefts, rights):
        if not lefts or not rights:
            return 1.0

        left_lang, lefts = lefts
        right_lang, rights = rights

        if right_lang != left_lang:
            return 1.0

        min_distance = 1.0
        for kwa, kwb in product(lefts, rights):
            # common = sum(1 for _ in takewhile(lambda t: t[0] == t[1], zip(kwa, kwb)))
            distance = 1.0 - len(kwa & kwb) / max(4, max(len(kwa), len(kwb)))
            min_distance = min(distance, min_distance)
            if float_cmp(distance, 0.0):
                break

        return 0.67 * min_distance + 0.33 * (not right_lang == left_lang)


if __name__ == '__main__':
    import sys
    import unittest

    class TestKeywordsDistance(unittest.TestCase):
        def test_basic(self):
            dist = KeywordsDistance()
            self.assertAlmostEqual(dist.do_compute(
                ('de', [frozenset(['a', 'b']), frozenset(['c', 'd'])]),
                ('de', [frozenset(['a', 'c']), frozenset(['b', 'd'])])
            ), 0.5025)
            self.assertAlmostEqual(dist.do_compute(
                ('de', [frozenset(['a', 'b']), frozenset(['c', 'd'])]),
                ('en', [frozenset(['a', 'x']), frozenset(['y', 'd'])])
            ), 1.0)
            self.assertAlmostEqual(dist.do_compute(
                ('de', [frozenset(['a', 'b']), frozenset(['c', 'd'])]),
                ('de', [frozenset(['a', 'b']), frozenset(['c', 'd'])])
            ), 0.335)
            self.assertAlmostEqual(dist.do_compute(
                ('de', [frozenset(['a', 'b', 'c', 'd']), frozenset(['c', 'd'])]),
                ('de', [frozenset(['a', 'b', 'c', 'd']), frozenset(['c', 'd'])])
            ), 0.0)
            self.assertAlmostEqual(dist.do_compute(
                ('de', [frozenset(['a', 'b']), frozenset(['c', 'd'])]),
                ('fr', [frozenset(['x', 'y']), frozenset(['z', 'ö'])]),
            ), 1.0)

    if '--cli' in sys.argv:
        from munin.provider import KeywordsProvider
        provider = KeywordsProvider()

        with open(sys.argv[2], 'r') as f:
            left_text = f.read()

        with open(sys.argv[3], 'r') as f:
            right_text = f.read()

        dist = KeywordsDistance()
        print(
            dist.do_compute(
                provider.do_process(left_text),
                provider.do_process(right_text)
            )
        )
    else:
        unittest.main()
