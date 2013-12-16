#!/usr/bin/env python
# encoding: utf-8

"""
Methods to traverse the graph in order to do recommendations.
"""
# Stdlib:
from itertools import chain, islice, zip_longest
from collections import deque
from math import ceil

import random


def sorted_breadth_first_search(start, n=0):
    """Iterator for a sorted (by distance) breadth first search.

    :param n: Number of items to yield at max. If 0, the whole graph is traversed.
    :returns: An iterator that will yield single songs, including the start song.
    """
    paths = deque([start])
    visited = set([start])

    yield start

    while paths:
        node = paths.popleft()
        for child in node.neighbors():
            if child not in visited:
                paths.append(child)
                visited.add(child)

                yield child

                if n is not 0 and len(visited) == n:
                    raise StopIteration


def recommendations_from_seed(database, rule_index, song, n=20):
    # Shortcuts:
    if n is 0:
        return iter([])

    if n is 1:
        return next(iter(song.neighbors()))

    return _recommendations_from_seed(database, rule_index, song, n=n)


# Generator implementation:
def _recommendations_from_seed(database, rule_index, seed_song, n=20):
    # Find rules, that affect this seed_song:
    associated = list(rule_index.lookup(seed_song))

    # No rules? Just use the seed_song as starting point...
    # One day, we will have rules. Shortcut for now.
    if not associated:
        bfs = sorted_breadth_first_search(seed_song, n=(n + 1))
        for recom in islice(bfs, 1, n + 1):
            yield recom
    else:
        # Create an iterator for each seed_song, in each associated rule:
        breadth_first_iters = deque()

        # We weight the number of songs max. given per iterator by their rating
        sum_rating = sum(rating for *_, rating in associated)

        # Now populate the list of breadth first iterators:
        for left, right, *_, rating in associated:
            # The maximum number that a single seed_song in this rule may
            # deliver (at least 1 - himself, therefore the ceil)
            bulk = right if seed_song in left else left

            # Calculate the maximum of numbers a bulk may yield.
            max_n = ceil(((rating / sum_rating) * (n // 2)) / len(bulk))
            if n is 0 or n == len(database):
                max_n *= 2
            else:
                max_n += 1

            # We take the songs in the opposite set of the rule:
            for bulk_song in bulk:
                breadth_first = sorted_breadth_first_search(bulk_song)
                breadth_first = islice(breadth_first, max_n)
                breadth_first_iters.append(breadth_first)

        # The result set will be build by half
        base_half = islice(
            sorted_breadth_first_search(seed_song),
            1,
            n // 2 + 1
        )

        # Yield the base half first:
        songs_set = set([seed_song])
        for recom in base_half:
            yield recom
            songs_set.add(recom)

        # Now build the final result set by filling one half original songs,
        # and one half songs that were pointed to by rules.
        for legion in zip_longest(*breadth_first_iters):
            for recom in filter(None, legion):
                # We have this already in the result set:
                if recom in songs_set:
                    continue

                songs_set.add(recom)
                yield recom

                if len(songs_set) > n:
                    raise StopIteration


def recommendations_from_attributes(subset, database, rule_index, n=20):
    try:
        chosen_song = next(database.find_matching_attributes(subset))
        return chain(
            [chosen_song],
            recommendations_from_seed(rule_index, chosen_song, n=n)
        )
    except StopIteration:
        return iter([])


def recommendations_from_heuristic(database, rule_index, n=20):
    best_rule = rule_index.best()
    if best_rule is not None:
        # First song of the rules' left side
        chosen_song = best_rule[0][0]
    else:
        (chosen_song, count), *_ = database.playcount(n=1)
        if count is 0:
            chosen_song = random.choice(database)

    return chain(
        [chosen_song],
        recommendations_from_seed(rule_index, chosen_song, n=n)
    )


def explain_recommendation(seed_song, recommendation, max_reasons=3):
    distance = seed_song.distance_compute(recommendation)
    return (distance, sorted(distance.items(), key=lambda tup: [1])[:max_reasons])


if __name__ == '__main__':
    import unittest

    from munin.testing import DummyDistanceFunction
    from munin.session import Session

    class TestNeighborsFrom(unittest.TestCase):
        def setUp(self):

            self._session = Session('test', {
                'genre': (None, DummyDistanceFunction(), 1.0)
            })

            self.N = 10
            with self._session.transaction():
                for idx in range(self.N):
                    self._session.add({'genre': self.N - idx})

            # self._session.database.plot()

        def test_neighbors_sorted(self):
            # Since no rules available, sorted_breadth_first_search will be called.
            rec = list(self._session.recommend_from_seed(self._session[0], number=self.N))
            self.assertEqual(len(rec), self.N - 1)
            self.assertEqual([r.uid for r in rec], list(range(1, self.N)))

            rec = list(self._session.recommend_from_seed(self._session[0], number=5))
            self.assertEqual(len(rec), 5)
            self.assertEqual([r.uid for r in rec], list(range(1, 6)))

        def test_recommend_with_rules(self):
            # Add two rules,
            # [0] <-> [100]  [0.75]
            # [0] <-> [50]   [0.50]
            self._session.rule_index.insert_rule((
                frozenset([self._session[+0]]),
                frozenset([self._session[-1]]),
                self.N // 10,
                0.75
            ))

            self._session.rule_index.insert_rule((
                frozenset([self._session[+0]]),
                frozenset([self._session[self.N // 2]]),
                self.N // 15,
                0.50
            ))

            rec = list(self._session.recommend_from_seed(self._session[0], number=self.N))
            self.assertEqual(len(rec), self.N - 1)
            self.assertEqual(
                [1, 2, 3, 4, 5, 9, 8, 7, 6],
                [r.uid for r in rec]
            )

            rec = list(self._session.recommend_from_seed(self._session[0], number=5))
            self.assertEqual(len(rec), 5)
            self.assertEqual(
                [1, 2, 9, 5, 8],
                [r.uid for r in rec]
            )

    unittest.main()
