#!/usr/bin/env python
# encoding: utf-8

from collections import deque, Counter
from time import time


class History:
    def __init__(self, maxlen=100):
        self._buffer = deque(maxlen=maxlen)

    def feed(self, song):
        self._buffer.append((song, time()))

    def clear(self):
        self._buffer.clear()

    def __iter__(self):
        return (song for song, tstmp in self._buffer)

    def count_keys(self):
        counter = Counter()
        for song in self:
            counter.update(song.keys())
        return counter

    def count_listens(self):
        counter = Counter()
        for song in self:
            counter[song] += 1

        return counter


class ListenHistory(History):
    def __init__(self):
        History.__init__(self, maxlen=500)


class RecomnendationHistory(History):
    def __init__(self):
        History.__init__(self, maxlen=100)


if __name__ == '__main__':
    from munin.song import Song
    from munin.session import Session
    from random import choice
    import unittest

    class HistoryTest(unittest.TestCase):
        def setUp(self):
            self._session = Session('test', {
                'a': (None, None, 1.0),
                'b': (None, None, 1.0),
                'c': (None, None, 1.0),
                'd': (None, None, 1.0),
                'e': (None, None, 1.0),
                'f': (None, None, 1.0)
            })

        def test_count_keys(self):
            history = History()
            for _ in range(1000):
                song = Song(self._session, {choice('abcdef'): 1.0})
                history.feed(song)

            counter = history.count_keys()
            for char in 'abdef':
                self.assertTrue(char in counter)

            self.assertEqual(sum(counter.values()), 100)
            # print(history.count_listens())

    unittest.main()
