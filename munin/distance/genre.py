#!/usr/bin/env python
# encoding: utf-8


from itertools import product
from munin.distance import Distance


# There does not seem to be a built-in for this.
float_cmp = lambda a, b: abs(a - b) < 0.00000000001


def compare_single_path(left, right):
    '''Compare a single path with another.

    :returns: The ratio of matching numbers to max. length of both.
    '''
    n = 0.0
    for l, r in zip(left, right):
        if l != r:
            break
        n += 1
    return 1 - n / (max(len(left), len(right)) or 1)


class GenreDistance(Distance):
    '''Distance Calculator for comparing two lists of GenrePaths.

    (Lists of GenrePaths as returned by the GenreTree Provider)
    '''
    def calculate_distance(self, lefts, rights):
        min_dist = 1.0
        for left, right in product(lefts, rights):
            min_dist = min(min_dist, compare_single_path(left, right))

            # Optimization: Often we get a high value early.
            if float_cmp(min_dist, 0.0):
                break

        return min_dist


if __name__ == '__main__':
    import unittest

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

            for left, right, result in inputs:
                self.assertTrue(
                        float_cmp(compare_single_path(left, right), result)
                        and
                        float_cmp(compare_single_path(right, left), result)
                )

    class TestGenreDistance(unittest.TestCase):
        def test_valid(self):
            calc = GenreDistance()

            def full_cross_compare(expected):
                self.assertTrue(float_cmp(calc.calculate_distance(a, b), expected))
                self.assertTrue(float_cmp(calc.calculate_distance(b, a), expected))
                self.assertTrue(float_cmp(calc.calculate_distance(a, a), 0.0))
                self.assertTrue(float_cmp(calc.calculate_distance(b, b), 0.0))

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
            calc = GenreDistance()
            self.assertTrue(float_cmp(calc.calculate_distance([], []), 1.0))
            self.assertTrue(float_cmp(calc.calculate_distance([], [(1, 0)]), 1.0))
            self.assertTrue(float_cmp(calc.calculate_distance([], ['berta']), 1.0))

            # Funny one (strings are iterable)
            self.assertTrue(float_cmp(calc.calculate_distance(['berta'], ['berta']), 0.0))

            # Passing a non-iterable:
            with self.assertRaises(TypeError):
                calc.calculate_distance([1], [2])

    unittest.main()
