#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Compute the distance of two wordslists by building the union of both
wordlists and dividing this through the max length of both.

Reference
---------
"""

# Stdlib:
from itertools import combinations

# Internal:
from munin.distance import DistanceFunction


class WordlistDistance(DistanceFunction):
    """Compare a list of words using average linkage.

    Takes: an iterable of words and compares them directly.
    """
    def do_compute(self, lefts, rights):
        union = lefts & rights
        if not union:
            return 1.0

        return 1.0 - (len(union) / (max(len(lefts), len(rights))))

if __name__ == '__main__':
    import unittest

    class TestWordlistDistance(unittest.TestCase):
        def test_cmp(self):
            dfunc = WordlistDistance()
            self.assertEqual(
                dfunc.do_compute(
                    frozenset(['berta']),
                    frozenset(['berte']),
                ),
                1.0
            )
            self.assertEqual(
                dfunc.do_compute(
                    frozenset(['berta', 'berte']),
                    frozenset(['berte']),
                ),
                0.5
            )
            self.assertEqual(
                dfunc.do_compute(
                    frozenset(['berta', 'berte']),
                    frozenset(['berta', 'berte']),
                ),
                0.0
            )
            self.assertEqual(
                dfunc.do_compute(
                    frozenset(['berte', 'berta']),
                    frozenset(['berte', 'berta']),
                ),
                0.0
            )

    unittest.main()
