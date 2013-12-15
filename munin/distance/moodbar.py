#!/usr/bin/env python
# encoding: utf-8


"""
Overview
--------

The Distance Function in this Module works with the following providers:

    * :class:`munin.provider.moodbar.MoodbarProvider`
    * :class:`munin.provider.moodbar.MoodbarMoodFileProvider`
    * :class:`munin.provider.moodbar.MoodbarAudioFileProvider`

**Technical Details:**

The individual attributes are weighted and computes as following:

+-------------------+---------+---------------------------------------------------------------+
|  Name             | Weight  | Formula                                                       |
+===================+=========+===============================================================+
| *diffsum*         |   0.135 | ``abs(v1 - v2) / 50``                                         |
+-------------------+---------+---------------------------------------------------------------+
| *histogram*       |   0.135 | ``1.0 - sum(a - b for a, b in lefts, rights) / 5 * 255``      |
+-------------------+---------+---------------------------------------------------------------+
| *dominant colors* |   0.63  | ``len(common) / max(len(lefts), len(rights))``                |
+-------------------+---------+---------------------------------------------------------------+
| *blackness*       |   0.05  | ``abs(v1 - v2) / 50``                                         |
+-------------------+---------+---------------------------------------------------------------+
| *average min/max* |   0.05  | ``abs(v1 - v2) / 255``                                        |
+-------------------+---------+---------------------------------------------------------------+
|                   |   1.0   |                                                               |
+-------------------+---------+---------------------------------------------------------------+

Reference
---------
"""

from munin.distance import DistanceFunction
from math import sqrt


class MoodbarDistance(DistanceFunction):
    """Distance Function that compares two MoodbarDescriptions."""
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
            hist_diff = sum(abs(a - b) for a, b in zip(left_chan.histogram, right_chan.histogram))
            distance -= 0.045 * (1.0 - hist_diff / (5 * 255))
            distance -= 0.045 * distf(left_chan.diffsum, right_chan.diffsum, 50)

        distance -= 0.025 * distf(ld.average_max, rd.average_max, 255)
        distance -= 0.025 * distf(ld.average_min, rd.average_min, 255)
        distance -= 0.050 * distf(ld.blackness, rd.blackness, 50)

        lkeys, rkeys = ld.dominant_colors.keys(), rd.dominant_colors.keys()
        if lkeys and rkeys:
            distance -= 0.63 * (len(lkeys & rkeys) / max(len(lkeys), len(rkeys)))

        # Good distances are in the range 0.3 - 0.5 usually
        # Therefore we handle lower values better.
        # http://www.arndt-bruenner.de/mathe/scripts/regr.htm
        # was used to calculate a polynom that scales these values.
        # This function goes through the following points:
        # 0      0
        # 0,25   0,125
        # 0,5    0,5
        # 0,75   0,875
        # 1      1
        #
        # The function is not 100% correct, so we clamp possible precision
        # errors into [0, 1]
        d2 = distance * distance
        d3 = d2 * distance
        return min(1.0, max(0, -2.666 * d3 + 4 * d2 - 0.3333 * distance))


if __name__ == '__main__':
    import unittest

    from munin.provider.moodbar import MoodbarDescription, MoodbarChannel

    class TestMoodbarDistance(unittest.TestCase):
        def test_equality(self):
            func = MoodbarDistance()

            description = MoodbarDescription(
                [
                    MoodbarChannel([0, 0, 0, 0, 0], 0),
                    MoodbarChannel([0, 0, 0, 0, 0], 0),
                    MoodbarChannel([0, 0, 0, 0, 0], 0)
                ],
                0,
                0,
                {
                    (0, 0, 0): 20,
                    (1, 1, 1): 19,
                    (2, 2, 2): 18,
                    (256, 256, 256): 0
                },
                100
            )

            self.assertAlmostEqual(
                func.do_compute([description], [description]),
                0.0
            )

            anti = MoodbarDescription(
                [
                    MoodbarChannel([0xff, 0xff, 0xff, 0xff, 0xff], 20),
                    MoodbarChannel([0xff, 0xff, 0xff, 0xff, 0xff], 20),
                    MoodbarChannel([0xff, 0xff, 0xff, 0xff, 0xff], 20)
                ],
                0xff,
                0xff,
                {
                    (12, 12, 12): 20,
                    (250, 250, 250): 19,
                    (3, 3, 3): 18,
                    (255, 255, 255): 0
                },
                0
            )

            self.assertAlmostEqual(func.do_compute([description], [anti]), 1.0)

    unittest.main()
