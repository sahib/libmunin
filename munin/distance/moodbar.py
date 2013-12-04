#!/usr/bin/env python
# encoding: utf-8

from munin.distance import DistanceFunction
import math


class MoodbarDistance(DistanceFunction):
    def __init__(self, provider):
        DistanceFunction.__init__(self, provider, 'Moodbar')

    def compute(self, lefts, rights):
        distance = 1.0
        ld, rd = lefts[0], rights[0]
        gower = lambda v1, v2, m: 1.0 - math.sqrt(min(1.0, abs(v1 - v2) / m))

        for left_chan, right_chan in zip(ld.channels, rd.channels):
            # lhist, rhist = left_chan.histogram.keys(), right_chan.histogram.keys()
            # if lhist and rhist:
            #     distance -= 0.05 * len(lhist & rhist) / max(len(lhist), len(rhist))

            distance -= 0.05 * gower(left_chan.diffsum, right_chan.diffsum, 50)
            # distance -= (0.05 / 3) * gower(left_chan.sd, right_chan.sd, 100)
            # distance -= (0.05 / 3) * gower(left_chan.mean, right_chan.mean, 150)

        distance -= 0.05 * gower(ld.average_max, rd.average_max, 255)
        distance -= 0.05 * gower(ld.average_min, rd.average_min, 255)
        distance -= 0.10 * gower(ld.blackness, rd.blackness, 50)

        # Possible Improvement: Use the count of the colors to improve the measure
        lkeys, rkeys = ld.dominant_colors.keys(), rd.dominant_colors.keys()
        if lkeys and rkeys:
            diff, count = 0, 0
            for color in lkeys & rkeys:
                a, b = ld.dominant_colors[color], rd.dominant_colors[color]
                diff += abs(a - b) / max(a, b)
                count += 1

            if count is not 0:
                print(diff/ max(len(lkeys), len(rkeys)))
                distance -= 0.55 * (diff / max(len(lkeys), len(rkeys)))
            # lensum = len(lkeys) + len(rkeys)
            # d = (len(lkeys & rkeys)) / (lensum * (lensum - 1)) / max(len(lkeys), len(rkeys))
            # distance -= 0.55 * d
        return distance
