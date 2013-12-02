#!/usr/bin/env python
# encoding: utf-8

'''
Methods to traverse the igraph graph in order to do recomnendations.
'''
# Stdlib:
from itertools import chain, cycle, islice, groupby
from math import ceil

# Internal:
from munin.utils import roundrobin


def neighbors_from_song(graph, song, n=0):
    '''Give `n` recommendations based on a breadth-first search starting on  `song`.

    The given recomnendations won't be ordered in any particular way.
    If you want that you should use :func:`neighbors_from_song_sorted`.

    :param graph: an `igrah.Graph` to select the neighbors from.
    :param song: The start of the breadth-first search.
    :param n: How many songs to return. Might return less songs. If 0, return all.
    :returns: A generator that will yield the next song and it's depth, including `song`.
    '''

    # Give us a new breadth first iterator:
    breadth_first = graph.bfsiter(song.uid, advanced=True)

    # Take n items from it and only fetch the song/depth from each item
    song_iter = (vertex['song'] for vertex, depth, _ in breadth_first)
    if n is 0:
        return song_iter
    else:
        return islice(song_iter, n)


def neighbors_from_song_sorted(graph, song, n=0):
    '''Mostly like :func:`neighbors_from_song`, but sort results.

    The sorting is done by sorting every individual depth before returning it.
    You should note that this may require sorting large lists for high `n`'s.
    (although small numbers, smaller than 100, should be no problem).

    :param graph: an `igrah.Graph` to select the neighbors from.
    :param song: The start of the breadth-first search.
    :param n: How many songs to return. Might return less songs. If 0, return all.
    :returns: A generator that will yield a song and the depth, including `song`.
    '''
    # Give us a new breadth first iterator:
    breadth_first = graph.bfsiter(song.uid, advanced=True)
    if n is 0:
        # Just fake many, many items, and hope we never reach that.
        n = 10e100

    # Sorted by depth, one group at a time:
    for depth, group in groupby(breadth_first, lambda tup: tup[1]):
        # Sort the group by it's distances to to the new song and it's parent:
        # Note: We truncate to n here, which may not give perfectly sorted results.
        # But this way we do not e.g sort the whole 32k list for depth=4 just for one song.
        group_list = list(islice(group, n))
        if len(group_list) > 1:
            group_list.sort(key=lambda tup: tup[0]['song'].distance_get(tup[2]['song']))

        # Now hand the new iteration results further.
        for vx, *_ in group_list:
            yield vx['song']
            if n is 1:
                return
            n -= 1


def common_recomnendations(graph, song_a, song_b, n=10):
    '''Find the common recommendations between two songs.

    This might be useful when we need to base recommendations on more than one song.

    With `n == 1`, there will be only results when `song_a` and `song_b` are neighbors.
    With `n == num_of_neighbors`, indirect neighbors will be found,
    and so on

    :param graph: The graph to traverse.
    :param song_a: One song to base recommendations to.
    :param song_b: Other song to base recommendations to.
    :param n: This is forwarded to :func:`neighbors_from_song`
    :returns: a generator that will yield many pairs of songs from each individual set.
    '''
    # Get the edges between the stars of song_a and song_b:
    edges = graph.es.select(_between=(
        [song for song, _ in neighbors_from_song(graph, song_a, n=n)],
        [song for song, _ in neighbors_from_song(graph, song_b, n=n)]
    ))

    return ((g.vs[edge.source], g.vs[edge.target]) for edge in edges)


def recomnendations_from_song(graph, rule_index, song, n=20):
    '''Give 'n' recomnendations based on 'song'.

    - Will lookup rules for song.
    - If no rules found, a breadth first search starting with song is
      performed.
    - Otherwise, breadth first from songs mentioned in the rules are done.

    :param graph: The graph to breadth first search on.
    :type graph: :class:`igraph.Graph`
    :param rule_index: Rule database.
    :type rule_index: :class:`munin.history.RuleIndex`
    :param song: Song to base recomnendations on.
    :type song: :class:`munin.song.Song`
    :param n: Deliver so many recomnendations (at max.)
    :returns: An iterator that yields recomnend songs.
    '''
    # Shortcuts:
    if n is 0:
        return []

    if n < 5:
        return list(song.distance_iter())[:n]

    # Find rules, that affect this song:
    associated = list(rule_index.lookup(song))

    # No rules? Just use the song as starting point...
    # One day, we will have rules. Shortcut for now.
    if not associated:
        for song in neighbors_from_song_sorted(graph, song, n=n):
            yield song
        return

    # Create an iterator for each song, in each associated rule:
    breadth_first_iters = deque()

    # We weight the number of songs max. given per iterator by their rating:
    sum_rating = sum(rating for *_, rating in associated)

    # Now populate the list of breadth first iterators:
    for left, right, *_, rating in associated:
        # The maximum number that a single song in this rule may deliver
        # (at least 1 - himself, therefore the ceil)
        max_n = ceil(((rating / sum_rating) * (n / 2)) / len(bulk))

        # We take the songs in the opposite set of the rule:
        for song in (right if song in left else left):
            breadth_first = islice(neighbors_from_song_sorted(graph, song)
            breadth_first_iters.append(breadth_first, max_n))

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


if __name__ == '__main__':
    # TODO: unittests
    pass
