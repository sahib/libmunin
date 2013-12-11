

"""This module contains common helpers used during unittests.
"""


# Mock the distance class
class DistanceDummy:
    def __init__(self, d):
        self.distance = d

    def __eq__(self, other):
        return self.distance == other.distance

    def __lt__(self, other):
        return self.distance > other.distance

    def __repr__(self):
        return str(self.distance)

    def __invert__(self):
        return 1.0 - self.distance
