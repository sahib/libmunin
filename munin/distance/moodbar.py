#!/usr/bin/env python
# encoding: utf-8

from munin.distance import DistanceFunction
from math import sqrt


class MoodbarDistance(DistanceFunction):
    def __init__(self, provider):
        DistanceFunction.__init__(self, provider, 'Moodbar')

    def compute(self, lefts, rights):
        distance = 1.0
        ld, rd = lefts[0], rights[0]
        distf = lambda v1, v2, m: 1.0 - sqrt(min(1.0, abs(v1 - v2) / m))

        for left_chan, right_chan in zip(ld.channels, rd.channels):
            hist_diff = sum(a - b for a, b in zip(left_chan.histogram, right_chan.histogram))
            distance -= 0.045 * (1.0 - hist_diff / (5 * 255))
            distance -= 0.045 * distf(left_chan.diffsum, right_chan.diffsum, 50)

        distance -= 0.025 * distf(ld.average_max, rd.average_max, 255)
        distance -= 0.025 * distf(ld.average_min, rd.average_min, 255)
        distance -= 0.050 * distf(ld.blackness, rd.blackness, 50)

        lkeys, rkeys = ld.dominant_colors.keys(), rd.dominant_colors.keys()
        if lkeys and rkeys:
            distance -= 0.63 * (len(lkeys & rkeys) / max(len(lkeys), len(rkeys)))
        return distance
