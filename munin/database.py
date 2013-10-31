#!/usr/bin/env python
# encoding: utf-8

from contextlib import contextmanager
from itertools import combinations


class Database:
    'Class managing Database concerns.'
    def __init__(self, session):
        '''
        .. note::

            The division of :class:`munin.Session` and :class:`Database`
            is purely cosmetical.
        '''
        self._session = session
        self._song_list = []

    def rebuild(self):
        for song_a, song_b in combinations(self._song_list):
            # Compute a Distane object:
            distance = song_a.distance_compute(song_b)

            # Adding works bidirectional:
            song_a.distance_add(song_b, distance)

    def add(self, song):
        if song is not None:
            self._song_list.append(song)

    @contextmanager
    def transaction(self):
        yield
        self.rebuild()


if __name__ == '__main__':
    import unittest

    class DatabaseTests(unittest.TestCase):
        def test_basic_attributes(self):
            pass

    unittest.main()
