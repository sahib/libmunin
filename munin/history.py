#!/usr/bin/env python
# encoding: utf-8

'''
.. todo:: Add a descriptive module text.
'''

# Stdlib:
from itertools import chain
from collections import deque, Counter
from time import time

# External:
from pymining import itemmining

###########################################################################
#                         Association Rule Mining                         #
###########################################################################


def append_rule(
        data, visited, rules, known_rules, support, left, right,
        min_confidence, min_kulc, max_ir
):
    '''Internal Function. Append a rule if it's good enoguh to `rules`.

    :param visited: Set of visited pairs.
    :param known_rules: Rules that are known, and do not need to be recaclulated.
    :param support: Support count for this rule.
    '''
    visited.add((left, right))
    if not all((right, left, right in data, left in data)):
        return

    if (left, right) in known_rules or (right, left) in known_rules:
        return

    supp_left = data.get(left)
    confidence = support / supp_left
    if confidence < min_confidence:
        return

    # Kulczynski Measure for consistent rule correlation.
    # [0, 1.0], higher is better.
    # Compare: "Data Mining - Concepts and Techniques" Page 268
    supp_right = data[right]
    kulc = (support / supp_right + support / supp_left) / 2
    if kulc < min_kulc:
        return

    # Imbalance Ratio of the Rule.
    # [0, 1.0], lower is better.
    # Compare: "Data Mining - Concepts and Techniques" Page 270
    ir = abs((supp_left - supp_right) / (supp_left + supp_right - support))
    if ir >= max_ir:
        return

    # Finally add the rule, after all those tests.
    rules.append((left, right, support, confidence, kulc, ir))

    # Lookup set, so we don't calculate the same rule more than once.
    known_rules.add((left, right))


def association_rules(data, min_confidence=0.5, min_support=2, min_kulc=0.66, max_ir=0.35):
    '''Compute strong association rules from the itemset_to_support dict in data.

    Inspiration for some tricks in this function were take from:

        https://github.com/bartdag/pymining/blob/master/pymining/assocrules.py

    :param data: Mapping between itemsets and support counts
    :type data: dict(set=int)
    :param min_confidence: Minimal confidence a rule must have (from 0 to 1, higher is better)
    :type min_confidence: float
    :param min_support: Minimal support an itemset must have.
                        Lowers ones are filtered out and only used for lookup.
    :type min_support: int
    :param min_kulc: Minimum Kulczynski measure (from 0 to 1, higher is better)
    :type min_kulc: float
    :param max_ir: Maximum Imbalance Ratio (from 0 to 1, lower is better)
    :type max_ir: float
    :returns: An iterable with rules.
    :rtype: [(left, right, support, confidence, kulc, ir), ...]
    '''
    visited, rules, known_rules = set(), deque(), set()

    # Sort data items by their size, large itemsets first:
    data_items = sorted((
        (itemset, supp) for itemset, supp in data.items()
        if supp >= min_support and len(itemset) > 1
    ), key=lambda tup: len(tup[0]))

    for itemset, support in data_items:
        # Now, build all (senseful) partions of the itemset:
        for item in itemset:
            # Start with one left=item, right=rest
            left, right = frozenset([item]), itemset.difference([item])

            while len(right) is not 0 and (left, right) not in visited:
                # We copy right, so it does not get harmed during iteration:
                for item in chain(right, [None]):
                    append_rule(
                            data, visited, rules, known_rules,
                            support, left, right, min_confidence,
                            min_kulc, max_ir
                   )
                    if item is not None:
                        cap = [item]
                        left, right = left.union(cap), right.difference(cap)

    return rules


###########################################################################
#                         History Implementation                          #
###########################################################################


class History:
    '''A History implements a mechanism to store groups of songs together
    that were listened in a certain order.

    Songs can be feeded to the history. Songs that were feeded at the same time
    get into the same group, after some time threshold has passed, a new group
    is opened. A group may only have a certain size, if the size is exceeded
    a new group is opened.

    The whole history can be set to store only a certain amount of groups.
    If new groups are added, the oldest ones are removed.
    '''
    def __init__(self, maxlen=100, time_threshold_sec=1200, max_group_size=5):
        '''Instance a new History object with these settings:

        :param maxlen: Max. number of groups that may be fed to the history.
        :param time_threshold_sec: Time after which a new group is opened, even
                                   if the current group is not yet full.
        :param max_group_size: Max. size of a single group.
        '''
        self._buffer = deque(maxlen=maxlen)
        self._current_group = []
        self._time_threshold_sec, self._max_group_size = time_threshold_sec, max_group_size

    def __iter__(self):
        'Iterate over all songs in the history'
        return chain.from_iterable(self.groups())

    def last_time(self):
        '''Gives the last inserted timestamp, or if empty, the current time'''
        # Check if we have a current group:
        if self._current_group:
            return self._current_group[-1][1]

        # Return the current time instead:
        return time()

    def feed(self, song):
        '''Feed a single song to the History.

        :param song: The song to add to the listen history.
        :type song: A :class:`munin.song.Song`
        '''
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
        '''Clear the history fully.

        Will be as freshly instantiated afterwards.
        '''
        self._buffer.clear()
        self._current_group = []

    def groups(self):
        '''Return an iterator to iterate over all groups in the History.

        :returns: an iterator that yields a list of iteralbes with songs in it.
        '''
        iterables = deque()
        for group in self._buffer:
            iterables.append((song for song, _ in group))

        if self._current_group:
            iterables.append((song for song, _ in self._current_group))

        return iterables

    def count_keys(self):
        '''Count the key distribution of the songs in the history

        Not all songs have all keys set.
        This can be helpful to find often missing data.

        :returns: A collections.Counter object with each attribute and their count.
        '''
        counter = Counter()
        for song in self:
            counter.update(song.keys())
        return counter

    def count_listens(self):
        '''Count the listens of the songs in the history

        :returns: A collections.Counter object with each song and their count.
        '''
        counter = Counter()
        for song in self:
            counter[song] += 1

        return counter

###########################################################################
#                        Concrete Implementations                         #
###########################################################################


class ListenHistory(History):
    '''A History that holds all recently listened Songs.
    '''
    def __init__(self):
        'Sane defaults are chosen for ``History.__init__``'
        History.__init__(self, maxlen=10000, max_group_size=5)

    def frequent_itemsets(self, min_support=2):
        relim_input = itemmining.get_relim_input(list(self.groups()))
        return itemmining.relim(relim_input, min_support=min_support)


class RecomnendationHistory(History):
    '''A History that holds all recently given recomnendations.
    '''
    def __init__(self):
        'Sane defaults are chosen for ``History.__init__``'
        History.__init__(self, maxlen=100)


###########################################################################
#                               Unit Tests                                #
###########################################################################

if __name__ == '__main__':
    from random import choice
    from unittest import TestCase, main
    from random import choice

    from munin.song import Song
    from munin.session import Session

    class HistoryTest(TestCase):
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
            history = ListenHistory()

            songs = [Song(self._session, {'abcdef'[idx]: 1.0}) for idx in range(6)]
            for idx, song in enumerate(songs):
                song.uid = idx

            N = 10
            for _ in range(N):
                for i, ilem in enumerate(songs):
                    history.feed(ilem)
                    for j, jlem in enumerate(songs[i:]):
                        history.feed(jlem)

            itemsets = history.frequent_itemsets()

            print()
            print('==================')
            print('FREQUENT ITEMSETS:')
            print('==================')
            print()
            for itemset, support in sorted(itemsets.items(), key=lambda x: x[1]):
                print('{: 8d} ({:0.3f}%): {:>20s}'.format(
                    support, support / N,
                    str([song.uid for song in itemset])
                ))

            print()
            print('==================')
            print('ASSOCIATION RULES:')
            print('==================')
            print()

            rules = association_rules(itemsets, min_support=2, min_confidence=0.3)
            sorted_rules = sorted(rules, key=lambda x: x[4], reverse=True)
            for left, right, support, confidence, kulc, irat in sorted_rules:
                print('{:>15s} <-> {:<15s} [supp={:> 5d}, conf={:.3f}, kulc={:.5f} irat={:.5f}]'.format(
                    str([song.uid for song in left]),
                    str([song.uid for song in right]),
                    support, confidence, kulc, irat
                ))

    main()
