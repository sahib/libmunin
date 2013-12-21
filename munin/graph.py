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

# Internal
from munin.helper import roundrobin


def sorted_breadth_first_search(start):
    """Iterator for a sorted (by distance) breadth first search.

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


def recommendations_from_seed(database, rule_index, seed_song):
    # Find rules, that affect this seed_song:
    associated = list(rule_index.lookup(seed_song))

    # No rules? Just use the seed_song as starting point...
    # One day, we will have rules. Shortcut for now.
    if not associated:
        bfs = sorted_breadth_first_search(seed_song)

        # Throw away first song:
        next(bfs)
        for recom in bfs:
            yield recom
    else:
        # Create an iterator for each seed_song, in each associated rule:
        breadth_first_iters = deque()

        # Now populate the list of breadth first iterators:
        for left, right, *_ in associated:
            # The maximum number that a single seed_song in this rule may
            # deliver (at least 1 - himself, therefore the ceil)
            bulk = right if seed_song in left else left

            # We take the songs in the opposite set of the rule:
            for bulk_song in bulk:
                breadth_first = sorted_breadth_first_search(bulk_song)
                breadth_first_iters.append(breadth_first)

        # The result set will be build by half
        base_half = sorted_breadth_first_search(seed_song)
        try:
            next(base_half)
        except StopIteration:
            pass

        # Yield the base half first:
        songs_set = set([seed_song])

        # Now build the final result set by filling one half original songs,
        # and one half songs that were pointed to by rules.
        for recom in roundrobin(base_half, roundrobin(*breadth_first_iters)):
            # We have this already in the result set:
            if recom in songs_set:
                continue
            else:
                songs_set.add(recom)

            yield recom


def recommendations_from_attributes(subset, database, rule_index):
    try:
        chosen_song = next(database.find_matching_attributes(subset))
        return chain(
            [chosen_song],
            recommendations_from_seed(database, rule_index, chosen_song)
        )
    except StopIteration:
        return iter([])


def recommendations_from_heuristic(database, rule_index):
    best_rule = rule_index.best()
    if best_rule is not None:
        # First song of the rules' left side
        chosen_song = next(iter(best_rule[0]))
    else:
        counts = database.playcounts(n=1)
        if len(counts):
            (chosen_song, cnt), *_ = counts
        else:
            chosen_song = random.choice(database)

    return chain(
        [chosen_song],
        recommendations_from_seed(database, rule_index, chosen_song)
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
                [1, 9, 2, 5, 3, 8, 4, 7, 6],
                [r.uid for r in rec]
            )

            rec = list(self._session.recommend_from_seed(self._session[0], number=5))
            self.assertEqual(len(rec), 5)
            self.assertEqual(
                [1, 9, 2, 5, 3],
                [r.uid for r in rec]
            )

    unittest.main()
