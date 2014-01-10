#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from itertools import product

# Internal:
from munin.distance import DistanceFunction
from munin.helper import float_cmp


def compare_single_path(left, right):
    """Compare a single path with another.

    :returns: The ratio of matching numbers divided by max. length of both.
    """
    n = 0.0
    for l, r in zip(left, right):
        if l != r:
            break
        n += 1
    return 1 - n / (max(len(left), len(right)) or 1)


class GenreTreeAvgLinkDistance(DistanceFunction):
    """
    Like :class:`munin.distance.genre.GenreTreeDistance`,
    but use Average Linkage instead of Single Linkage.

    This is recommended if you have long genre descriptions, like
    produced by :class:`munin.provider.genre.DiscogsGenreProvider`.
    """
    def do_compute(self, lefts, rights):
        if not lefts or not rights:
            return 1.0

        dist_sum = 0
        for left, right in product(lefts, rights):
            dist_sum += compare_single_path(left, right)
        return dist_sum / (len(lefts) * len(rights))


class GenreTreeDistance(DistanceFunction):
    """DistanceFunction Calculator for comparing two lists of GenrePaths.

    (Lists of GenrePaths as returned by the GenreTree Provider)
    """
    def do_compute(self, lefts, rights):
        """Calculate distance between two genre paths by using complete linkage.

        :param lefts: A list of Genre Paths.
        :param rights: A list of Genre Paths to compare with.
        :returns: A distance between 0.0 and 1.0 (max diversity.)
        """
        min_dist = 1.0
        for left, right in product(lefts, rights):
            min_dist = min(min_dist, compare_single_path(left, right))

            # Optimization: Often we get a low value early.
            if float_cmp(min_dist, 0.0):
                break

        return min_dist


if __name__ == '__main__':
    import unittest
    from munin.provider.genre import GenreTreeProvider

    class TestSinglePathCompare(unittest.TestCase):
        def test_valid(self):
            inputs = [
                ((190, 1, 0), (190, 1, 0), 0),
                ((190, 1, 0), (190, 1, 1), 1 / 3),
                ((190, 0, 1), (190, 1, 0), 2 / 3),
                ((190, 0, 1), (191, 1, 0),  1),
                ((190, 0, 1), (190, 0, 1, 0), 1 / 4),
                ((190, ), (), 1),
                ((), (), 1)
            ]

            calc = GenreTreeDistance(GenreTreeProvider())
            for left, right, result in inputs:
                self.assertTrue(
                        float_cmp(compare_single_path(left, right), result)
                        and
                        float_cmp(compare_single_path(right, left), result)
                )

    class TestGenreTreeDistanceFunction(unittest.TestCase):
        def test_valid(self):
            calc = GenreTreeDistance(GenreTreeProvider())

            def full_cross_compare(expected):
                self.assertTrue(float_cmp(calc.compute(a, b), expected))
                self.assertTrue(float_cmp(calc.compute(b, a), expected))
                self.assertTrue(float_cmp(calc.compute(a, a), 0.0))
                self.assertTrue(float_cmp(calc.compute(b, b), 0.0))

            a = [(85, 0), (190, 2), (190, 6)]
            b = [(85, 0), (190, 2, 0), (190, 2, 1), (190, 6)]
            full_cross_compare(0.0)

            a = [(1, 0), (0, 1)]
            b = [(0, 0), (1, 0)]
            full_cross_compare(0.0)

            a = [(0, 1)]
            b = [(1, 0)]
            full_cross_compare(1.0)

            a = [(1, 0)]
            b = [(1, 1)]
            full_cross_compare(0.5)

        def test_invalid(self):
            'Test rather unusual corner cases'
            calc = GenreTreeDistance(GenreTreeProvider())
            self.assertTrue(float_cmp(calc.compute([], []), 1.0))
            self.assertTrue(float_cmp(calc.compute([], [(1, 0)]), 1.0))
            self.assertTrue(float_cmp(calc.compute([], ['berta']), 1.0))

            # Funny one (strings are iterable)
            self.assertTrue(float_cmp(calc.compute(['berta'], ['berta']), 0.0))

            # Passing a non-iterable:
            with self.assertRaises(TypeError):
                calc.compute([1], [2])

        def test_rule(self):
            calc = GenreTreeDistance(GenreTreeProvider())
            self.assertAlmostEqual(calc.compute([(1, 0, 1)], [(0, 1, 0)]), 1.0)
            self.assertAlmostEqual(calc.compute([(1, 0, 0)], [(1, 1, 1)]), 2 / 3)

            self.assertAlmostEqual(calc.compute([(1, 1)], [(1, 1)]), 0.0)
            self.assertAlmostEqual(calc.compute([(1, 1)], [(2, 0)]), 1.0)

    unittest.main()
