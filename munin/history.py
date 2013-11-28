#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from itertools import chain
from collections import deque, Counter
from time import time

# External:
from pymining import itemmining, assocrules


class History:
    def __init__(self, maxlen=100, time_threshold_sec=3600, max_group_size=5):
        self._buffer = deque(maxlen=maxlen)
        self._current_group = []
        self._time_threshold_sec, self._max_group_size = time_threshold_sec, max_group_size

    def last_time(self):
        if self._current_group:
            return self._current_group[-1][1]

        # Return the current time instead:
        return time()

    def feed(self, song):
        # Check if we need to clear the current group:
        exceeds_size = len(self._current_group) >= self._max_group_size
        exceeds_time = abs(time() - self.last_time()) >= self._time_threshold_sec

        if exceeds_size or exceeds_time:
            # Add the buffer to the grouplist,
            self._buffer.append(self._current_group)
            self._current_group = []

        # Append a tuple of song and the current time:
        self._current_group.append((song, time()))

    def clear(self):
        self._buffer.clear()
        self._current_group = []

    def groups(self):
        iterables = deque()
        for group in self._buffer:
            iterables.append((song for song, _ in group))

        if self._current_group:
            iterables.append((song for song, _ in self._current_group))

        return iterables

    def __iter__(self):
        return chain.from_iterable(self.groups())

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
        History.__init__(self, maxlen=10000, max_group_size=10)

    def frequent_itemsets(self):
        # return fp_growth.find_frequent_itemsets(self.groups(), 2, include_support=True)

        relim_input = itemmining.get_relim_input(list(self.groups()))
        report = itemmining.relim(relim_input, min_support=2)
        return report


class RecomnendationHistory(History):
    def __init__(self):
        History.__init__(self, maxlen=100)


if __name__ == '__main__':
    from munin.song import Song
    from munin.session import Session
    from random import choice
    import unittest
    from random import choice

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
            history = History(maxlen=19)
            for _ in range(2000):
                history.feed(Song(self._session, {choice('abcdef'): 1.0}))

            counter = history.count_keys()
            for char in 'abdef':
                self.assertTrue(char in counter)

            self.assertEqual(sum(counter.values()), 100)
            self.assertEqual(len(list(history.groups())), 20)
            for group in history.groups():
                self.assertEqual(len(list(group)), 5)
            # print(history.count_listens())

        def test_fpgrowth(self):
            songs = [Song(self._session, {'abcdef'[idx]: 1.0}) for idx in range(6)]
            for idx, song in enumerate(songs):
                song.uid = idx

            history = ListenHistory()

            # for _ in range(1000):
            #     history.feed(choice(songs))

            # print(len(list(history.groups())))
            # print(list(list(history.groups())[1]))
            N = 1
            for _ in range(N):
                for i, ilem in enumerate(songs):
                    history.feed(ilem)
                    for j, jlem in enumerate(songs[i:]):
                        history.feed(jlem)

            # print(list(history.groups()))
            itemsets = history.frequent_itemsets()
            for itemset, support in sorted(itemsets.items(), key=lambda x: x[1]):
                print('{: 8d} ({:0.3f}%): {:>20s}'.format(
                    support, support / N,
                    [song.uid for song in itemset]
                ))

            rules = assocrules.mine_assoc_rules(itemsets, min_support=2, min_confidence=0.5)
            for rule in rules:
                print(rule)

    unittest.main()
