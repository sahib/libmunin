#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from itertools import product

# Internal:
from munin.distance import DistanceFunction


# TODO
class WordlistDistance(DistanceFunction):
    def do_compute(self, lefts, rights):
        max_both = max(len(lefts), len(rights))
        if max_both is 0:
            return 1.0

        return sum(a == b for a, b in product(lefts, rights)) / max_both

if __name__ == '__main__':
    import unittest

    class TestWordlistDistance(unittest.TestCase):
        def test_cmp(self):
            dfunc = WordlistDistance()
            self.assertEqual(
                dfunc.do_compute(('berta', ), ('berte', )), 0.0
            )
            self.assertEqual(
                dfunc.do_compute(('berta', 'berte'), ('berte', )), 0.5
            )
            self.assertEqual(
                dfunc.do_compute(('berta', 'berte'), ('berta', 'berte')), 1.0
            )
            self.assertEqual(
                dfunc.do_compute(('berte', 'berta'), ('berte', 'berta')), 1.0
            )

    unittest.main()
