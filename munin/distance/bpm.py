#!/usr/bin/env python
# encoding: utf-8


from munin.distance import DistanceFunction


class BPMDistance(DistanceFunction):
    """Distance Function that compares two Beats Per Minute Lists.

    This DistanceFunction works with the following providers:

        * :class:`munin.provider.bpm.BPMProvider`
        * :class:`munin.provider.bpm.BPMCachedProvider`
    """
    def do_compute(self, lefts, rights):
        max_n = 250
        return abs(max(lefts[0], max_n) - max(rights[0], max_n)) / max_n
