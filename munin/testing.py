

"""This module contains common helpers used during unittests.
"""

from munin.distance import DistanceFunction


# Mock the distance class
class DistanceDummy:
    def __init__(self, d):
        self.distance = d

    def __eq__(self, other):
        return self.distance == other.distance

    def __lt__(self, other):
        return self.distance < other.distance

    def __repr__(self):
        return str(self.distance)

    def __invert__(self):
        return 1.0 - self.distance


class DummyDistanceFunction(DistanceFunction):
    def compute(self, list_a, list_b):
        a, b = list_a[0], list_b[0]
        maxab = max(a, b)
        if maxab > 1.0:
            return abs(a - b) / maxab
        else:
            return abs(a - b)
