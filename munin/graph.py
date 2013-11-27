#!/usr/bin/env python
# encoding: utf-8

'''
Methods to traverse the igraph graph in order to do recomnendations.
'''

from itertools import chain, islice, groupby


def recomnendations_from_song(graph, song, n=10):
    '''Give `n` recommendations based on a breadth-first search starting on  `song`.

    The given recomnendations won't be ordered in any particular way.
    If you want that you should use :func:`recomnendations_from_song_sorted`.

    :param graph: an `igrah.Graph` to select the neighbors from.
    :param song: The start of the breadth-first search.
    :param n: How many songs to return. Might return less songs.
    :returns: A generator that will yield the next song and it's depth, including `song`.
    '''
    # Give us a new breadth first iterator:
    breadth_first = graph.bfsiter(song.uid, advanced=True)

    # Take n items from it and only fetch the song/depth from each item
    return islice(((vertex['song'], depth) for vertex, depth, _ in breadth_first), n)


def recomnendations_from_song_sorted(graph, song, n=10):
    '''Mostly like :func:`recomnendations_from_song`, but sort results.

    The sorting is done by sorting every individual depth before returning it.
    You should note that this may require sorting large lists for high `n`'s.
    (although small numbers, smaller than 100, should be no problem).

    :param graph: an `igrah.Graph` to select the neighbors from.
    :param song: The start of the breadth-first search.
    :param n: How many songs to return. Might return less songs.
    :returns: A generator that will yield a song and the depth, including `song`.
    '''
    # Give us a new breadth first iterator:
    breadth_first = graph.bfsiter(song.uid, advanced=True)

    # Sorted by depth, one group at a time:
    for depth, group in groupby(breadth_first, lambda tup: tup[1]):
        # Sort the group by it's distances to to the new song and it's parent:
        # Note: We truncate to n here, which may not give perfectly sorted results.
        # But this way we do not e.g sort the whole 32k list for depth=4 just for one song.
        group_list = list(islice(group, n))
        if len(group_list) > 1:
            group_list.sort(key=lambda tup: tup[0]['song'].distance_get(tup[2]['song']))

        # Now hand the new iteration results further.
        for vx, depth, parent in group_list:
            yield vx['song'], depth
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
    :param n: This is forwarded to :func:`recomnendations_from_song`
    :returns: a generator that will yield many pairs of songs from each individual set.
    '''
    # Get the edges between the stars of song_a and song_b:
    edges = graph.es.select(_between=(
        [song for song, _ in recomnendations_from_song(graph, song_a, n=n)],
        [song for song, _ in recomnendations_from_song(graph, song_b, n=n)]
    ))

    return ((g.vs[edge.source], g.vs[edge.target]) for edge in edges)
