#!/usr/bin/env python
# encoding: utf-8

from munin.distance import DistanceFunction


class MoodbarDistance(DistanceFunction):
    def __init__(self, provider):
        DistanceFunction.__init__(self, provider, 'Moodbar')

    def compute(self, lefts, rights):
        distance = 1.0
        ld, rd = lefts[0], rights[0]
        for left_chan, right_chan in zip(ld.channels, rd.channels):
            pass

        # http://de.wikipedia.org/wiki/Hierarchische_Clusteranalyse#Distanz-_und_.C3.84hnlichkeitsma.C3.9Fe
