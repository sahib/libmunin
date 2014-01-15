#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Calculate a distance from two years.

As minimal year *1970* is assumed.

Example Usage
-------------

.. code-block:: python

    >>> from munin.distance import DateDistance
    >>> dfunc = DateDistance()
    >>> dfunc.do_compute((1970,), (2014))
    1.0
    >>> dfunc.do_compute((1970,), (1970))
    0.0
    >>> dfunc.do_compute((2014,), (1992))
    0.5

Reference
---------

.. autoclass:: munin.distance.date.DateDistance
    :members:
"""

# Stdlib:
from datetime import date

# External:
from munin.distance import DistanceFunction


class DateDistance(DistanceFunction):
    """Compare the distance of two years, map them inbetween [0.0, 1.0]
    """
    def __init__(self, **kwargs):
        """
        As minimal year 1970 is assumed, as maximal year the current year.
        """
        DistanceFunction.__init__(self, **kwargs)
        self._min, self._now = 1970, date.today().year
        self._max_diff = (self._now - self._min) or 1

    def do_compute(self, lefts, rights):
        left, right = lefts[0], rights[0]
        diff = abs(left - right) / self._max_diff
        return max(0.0, min(1.0, diff))


if __name__ == '__main__':
    import unittest

    class DateDistanceTest(unittest.TestCase):
        def test_date(self):
            dfunc = DateDistance()
            this = date.today().year
            self.assertAlmostEqual(dfunc.do_compute((1970, ), (this, )), 1.0)
            self.assertAlmostEqual(dfunc.do_compute((this, ), (1970, )), 1.0)
            self.assertAlmostEqual(dfunc.do_compute((this, ), (this, )), 0.0)
            self.assertAlmostEqual(dfunc.do_compute((1970, ), (1970, )), 0.0)
            self.assertAlmostEqual(dfunc.do_compute((this, ), (this - (this - 1970) // 2, )), 0.5)

    unittest.main()
