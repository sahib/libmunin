#!/usr/bin/env python
# encoding: utf-8

"""
Overview
========

A very simple Distance Function that is suitable for the output of:

    * :class:`munin.provider.bpm.BPMProvider`
    * :class:`munin.provider.bpm.BPMCachedProvider`

50 is taken as the minum value, 250 as the maximum value.
(Although some songs may go up to 300)

Reference
=========
"""


from munin.distance import DistanceFunction


class BPMDistance(DistanceFunction):
    """Distance Function that compares two Beats Per Minute Lists."""
    def do_compute(self, lefts, rights):
        max_n = 200
        left, right = max(0, lefts[0] - 50), max(0, rights[0] - 50)
        return abs(max(left, max_n) - max(right, max_n)) / max_n
