#!/usr/bin/env python
# encoding: utf-8

"""
Methods to traverse the igraph graph in order to do recommendations.
"""
# Stdlib:
from itertools import chain, islice, groupby
from collections import deque
from math import ceil

import random

# Internal:
from munin.helper import roundrobin


def neighbors_from_song(graph, song, n=0):
    """Give `n` recommendations based on a breadth-first search starting on `song`.

    The given recommendations won't be ordered in any particular way.
    If you want that you should use :func:`neighbors_from_song_sorted`.

    :param graph: an `igrah.Graph` to select the neighbors from.
    :param song: The start of the breadth-first search.
    :param n: How many songs to return. Might return less songs. If 0, return all.
    :returns: A generator that will yield the next song and it's depth, including `song`.
    """
    # Give us a new breadth first iterator:
    breadth_first = graph.bfsiter(song.uid, advanced=True)
    # print(list(graph.bfsiter(song.uid, advanced=True)))

    # Take n items from it and only fetch the song/depth from each item
    song_iter = (vertex['song'] for vertex, depth, _ in breadth_first)
    if n < 1:
        return song_iter
    else:
        return islice(song_iter, n)


def neighbors_from_song_sorted(graph, song, n=0):
    """Mostly like :func:`neighbors_from_song`, but sort results.

    The sorting is done by sorting every individual depth before returning it.
    You should note that this may require sorting large lists for high `n`'s.
    (although small numbers, smaller than 100, should be no problem).

    :param graph: an `igrah.Graph` to select the neighbors from.
    :param song: The start of the breadth-first search.
    :param n: How many songs to return. Might return less songs. If 0, return all.
    :returns: A generator that will yield a song and the depth, including `song`.
    """
    # Give us a new breadth first iterator:
    breadth_first = graph.bfsiter(song.uid, advanced=True)
    if n is 0:
        # Just fake many, many items, and hope we never reach that.
        n = 10e100

    print(len(list(graph.bfsiter(song.uid, advanced=True))))

    # Sorted by depth, one group at a time:
    for depth, group in groupby(breadth_first, lambda tup: tup[1]):
        # Sort the group by it's distances to to the new song and it's parent:
        # Note: We truncate to n here, which may not give perfectly sorted results.
        # But this way we do not e.g sort the whole 32k list for depth=4 just for one song.
        group_list = list(islice(group, n))
        if len(group_list) > 1:
            group_list.sort(key=lambda tup: tup[0]['song'].distance_get(tup[2]['song']))

        # Now hand the new iteration results further.
        for vertex, *_ in group_list:
            yield vertex['song']
            if n is 1:
                raise StopIteration
            n -= 1


def common_neighbors(graph, song_a, song_b, n=10):
    """Find the common recommendations between two songs.

    This might be useful when we need to base recommendations on more than one song.

    With `n == 1`, there will be only results when `song_a` and `song_b` are neighbors.
    With `n == num_of_neighbors`, indirect neighbors will be found,
    and so on

    :param graph: The graph to traverse.
    :param song_a: One song to base recommendations to.
    :param song_b: Other song to base recommendations to.
    :param n: This is forwarded to :func:`neighbors_from_song`
    :returns: a generator that will yield many pairs of songs from each individual set.
    """
    # Get the edges between the stars of song_a and song_b:
    edges = graph.es.select(_between=(
        [song for song, _ in neighbors_from_song(graph, song_a, n=n)],
        [song for song, _ in neighbors_from_song(graph, song_b, n=n)]
    ))

    for edge in edges:
        yield (graph.vs[edge.source]['song'], graph.vs[edge.target]['song'])


def recommendations_from_seed(graph, rule_index, song, n=20):
    # Shortcuts:
    if n is 0:
        return iter([])

    if n < 5:
        return iter(list(song.distance_iter())[:n])

    return _recommendations_from_seed(graph, rule_index, song, n=n)


# Generator implementation:
def _recommendations_from_seed(graph, rule_index, song, n=20):
    # Find rules, that affect this song:
    associated = list(rule_index.lookup(song))

    print(associated, n)

    # No rules? Just use the song as starting point...
    # One day, we will have rules. Shortcut for now.
    if not associated:
        print('no rules', n)
        for song in neighbors_from_song_sorted(graph, song, n=n):
            yield song
    else:
        # Create an iterator for each song, in each associated rule:
        breadth_first_iters = deque()

        # We weight the number of songs max. given per iterator by their rating:
        sum_rating = sum(rating for *_, rating in associated)

        # Now populate the list of breadth first iterators:
        for left, right, *_, rating in associated:
            # The maximum number that a single song in this rule may deliver
            # (at least 1 - himself, therefore the ceil)
            bulk = right if song in left else left
            max_n = ceil(((rating / sum_rating) * (n / 2)) / len(bulk))

            # We take the songs in the opposite set of the rule:
            for song in bulk:
                breadth_first = islice(neighbors_from_song_sorted(graph, song), max_n)
                breadth_first_iters.append(breadth_first)

        # The result set will be build by half
        base_half = islice(neighbors_from_song_sorted(graph, song), 1, n / 2 + 1)
        songs_set = set()

        # Now build the final result set by filling one half original songs,
        # and one half songs that were pointed to by rules.
        for song in chain(base_half, roundrobin(breadth_first_iters)):
            # We have this already in the result set:
            if song in songs_set:
                continue

            songs_set.add(song)
            yield song

            if len(songs_set) >= n:
                break


def recommendations_from_attributes(subset, database, graph, rule_index, n=20):
    try:
        chosen_song = next(database.find_matching_attributes(subset))
        return chain(
            [chose_song],
            recommendations_from_seed(graph, rule_index, chosen_song, n=n)
        )
    except StopIteration:
        return iter([])


def recommendations_from_heuristic(database, graph, rule_index, n=20):
    try:
        # Get the best rule from the index
        best_rule = next(iter(rule_index))

        # First song of the rules' left side
        chosen_song = best_rule[0][0]
    except StopIteration:
        (chosen_song, count), *_ = database.playcount(n=1)
        if count is 0:
            chosen_song = random.choice(graph.vs)['song']

    return chain(
        [chosen_song],
        recommendations_from_seed(graph, rule_index, chosen_song, n=n)
    )


def explain_recommendation(seed_song, recommendation, max_reasons=3):
    distance = seed_song.distance_compute(recommendation)
    return (distance, sorted(distance.items(), key=lambda tup: [1])[:max_reasons])


if __name__ == '__main__':
    import unittest
    from itertools import combinations

    import igraph

    from munin.testing import DistanceDummy, DummyDistanceFunction
    from munin.song import Song
    from munin.session import Session

    class TestNeighborsFrom(unittest.TestCase):
        def setUp(self):

            self._session = Session('test', {
                'genre': (None, DummyDistanceFunction(), 1.0)
            })

            self.N = 100
            with self._session.transaction():
                for idx in range(self.N):
                    self._session.add({'genre': self.N - idx})

            self._session.database.plot()

            # edges = set()
            # for song_a, song_b in combinations(self._songs, 2):
            #     a, b = song_a.uid, song_b.uid
            #     Song.distance_add(song_a, song_b, DistanceDummy((a + b) / (2 * self.N)))
            #     if a < b:
            #         edges.add((a, b))
            #     else:
            #         edges.add((b, a))
            # self._graph.add_edges(list(edges))

        def test_neighbors(self):
            # rec = list(neighbors_from_song(self._graph, self._songs[0], n=self.N))
            rec = list(self._session.recommend_from_seed(self._session[0], number=self.N))
            print(len(rec), rec)
            self.assertTrue(rec)
            # self.assertEqual(set(rec), set(iter(self._session)))
            for song in rec:
                print(song.uid)

        def test_neighbors_sorted(self):
            #rec = list(neighbors_from_song_sorted(self._graph, self._songs[0], n=10))
            #self.assertEqual(rec[1:], sorted(self._songs[1:], key=lambda s: s.uid, reverse=True))
            #for song in rec:
            #    print(song.uid)
            pass

    unittest.main()
