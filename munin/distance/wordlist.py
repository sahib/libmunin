#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Compute the distance of two wordslists using Average-Link.

.. todo:: How is this different to the default distance?

Reference
---------
"""

# Stdlib:
from itertools import product

# Internal:
from munin.distance import DistanceFunction


class WordlistDistance(DistanceFunction):
    """Compare a list of words using complete link distance.

    Takes: an iterable of words and compares them directly.
    """
    def do_compute(self, lefts, rights):
        max_both = max(len(lefts), len(rights))
        if max_both is 0:
            return 1.0

        return 1.0 - sum(a == b for a, b in product(lefts, rights)) / max_both

if __name__ == '__main__':
    import unittest

    class TestWordlistDistance(unittest.TestCase):
        def test_cmp(self):
            dfunc = WordlistDistance()
            self.assertEqual(
                dfunc.do_compute(('berta', ), ('berte', )), 1.0
            )
            self.assertEqual(
                dfunc.do_compute(('berta', 'berte'), ('berte', )), 0.5
            )
            self.assertEqual(
                dfunc.do_compute(('berta', 'berte'), ('berta', 'berte')), 0.0
            )
            self.assertEqual(
                dfunc.do_compute(('berte', 'berta'), ('berte', 'berta')), 0.0
            )

    unittest.main()
