#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Compare the usergiven rating of a song with each other.

You can define the maximun and minimal rating. The same rating will give
a distance of 0.0.

Reference
---------
"""


from munin.distance import DistanceFunction


class RatingDistance(DistanceFunction):
    """Instance a new RatingDistance.
    """
    # Default to "5 stars"
    def __init__(self, no_rating=0, min_rating=1, max_rating=5, **kwargs):
        """
        :param no_rating: The rating that unrated songs will have, e.g. 0 stars.
        :param min_rating: The minimal rating you will have e.g. 1 stars.
        :param max_rating: The maximal rating you will have e.g. 5 stars.
        """
        DistanceFunction.__init__(self, **kwargs)

        self._min_rating = min_rating
        self._max_rating = max_rating
        self._no_rating = no_rating

    def do_compute(self, lefts, rights):
        l_rating = min(lefts[0], self._max_rating)
        r_rating = min(rights[0], self._max_rating)

        if l_rating == self._no_rating or r_rating == self._no_rating:
            if l_rating == r_rating:
                return 0.0
            else:
                return 0.5

        diff = abs((l_rating - self._min_rating) - (r_rating - self._min_rating))
        return diff / (self._max_rating - self._min_rating)


if __name__ == '__main__':
    import unittest

    class TestRatingDistance(unittest.TestCase):
        def test_rating(self):
            dfunc = RatingDistance()
            self.assertAlmostEqual(dfunc.do_compute([0.0], [0]), 0.0)
            self.assertAlmostEqual(dfunc.do_compute([0.0], [5]), 0.5)
            self.assertAlmostEqual(dfunc.do_compute([1.0], [5]), 1.0)
            self.assertAlmostEqual(dfunc.do_compute([5.0], [5]), 0.0)
            self.assertAlmostEqual(dfunc.do_compute([2.5], [5]), 0.625)

    unittest.main()
