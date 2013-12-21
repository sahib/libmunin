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


class KeywordsDistance(DistanceFunction):
    """
    The algorithm goes as follows:

        1) Build all products of keywordsets in both sides.
        2) :math:`counts(A, B) = \\sum 1 - \\frac{\|a \\cup b\|}{\\max{\|a\|, \|b\|}} \\forall a, b \\in A \\times B`
        3) :math:`distance(A, B) = \\frac{counts(A, B)}{\|A\| \\cdot \|B\|}`

    """
    def do_compute(self, lefts, rights):
        if not lefts or not rights:
            return 1.0

        count = 0
        for kwa, kwb in product(lefts, rights):
            if kwa and kwb:
                count += 1.0 - (len(kwa & kwb) / max(len(kwa), len(kwb)))
            else:
                count += 1.0

        return count / (len(lefts) * len(rights))
