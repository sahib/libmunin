#!/usr/bin/env python
# encoding: utf-8


from itertools import product
from munin.distance import DistanceFunction
from munin.utils import float_cmp


class AtticDistance(DistanceFunction):
    def __init__(self, provider):
        DistanceFunction.__init__(self, provider, 'GenreTree')

    def calculate_distance(self, lefts, rights):
        '''Calculate distance between two genre paths by using complete linkage.

        :param lefts: A list of Genre Paths.
        :param rights: A list of Genre Paths to compare with.
        :returns: A distance between 0.0 and 1.0 (max diversity.)
        '''
        pass


if __name__ == '__main__':
    import unittest

    class TestGenreTreeDistance(unittest.TestCase):
        def test_valid(self):
            pass
    unittest.main()
