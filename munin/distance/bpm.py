#!/usr/bin/env python
# encoding: utf-8

"""
Overview
========

A very simple Distance Function that is suitable for the output of:

    * :class:`munin.provider.bpm.BPMProvider`
    * :class:`munin.provider.bpm.BPMCachedProvider`

**Technical Details:**

The Distance as calculated as: ::

    abs(max(left_bpm, 250) - max(right_bpm, 250)) / 250

250 is usually the maximum value you will have.
(Although some songs may go up to 300)

Reference
=========
"""


from munin.distance import DistanceFunction


class BPMDistance(DistanceFunction):
    """Distance Function that compares two Beats Per Minute Lists."""
    def do_compute(self, lefts, rights):
        max_n = 250
        return abs(max(lefts[0], max_n) - max(rights[0], max_n)) / max_n
