#!/usr/bin/env python
# encoding: utf-8


from munin.distance import DistanceFunction
from math import sqrt


class MoodbarDistance(DistanceFunction):
    """Distance Function that compares two MoodbarDescriptions.

    This DistanceFunction works with the following providers:

        * :class:`munin.provider.moodbar.MoodbarProvider`
        * :class:`munin.provider.moodbar.MoodbarMoodFileProvider`
        * :class:`munin.provider.moodbar.MoodbarAudioFileProvider`
    """
    def do_compute(self, lefts, rights):
        """Compute the distance between two moodbar desc

        Only the first element in the individual lists is used.

        :param lefts: Packed left moodbar description.
        :param rights: Packed right moodbar description.
        """
        if not (lefts and rights):
            return 1.0

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

        # Good distances are in the range 0.3 - 0.5 usually
        # Therefore we handle lower values better:
        return 1.0 - sqrt(1.0 - distance)


if __name__ == '__main__':
    import unittest

    class TestMoodbarDistance(unittest.TestCase):
        def test_equality(self):
            # TODO: write test
            pass

    unittest.main()
