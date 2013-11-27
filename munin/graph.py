#!/usr/bin/env python
# encoding: utf-8

'''
Methods to traverse the igraph graph in order to do recomnendations.
'''

from itertools import chain, islice, groupby


def recomnendations_from_song(graph, song, n=10):
    # Give us a new breadth first iterator:
    breadth_first = graph.bfsiter(song.uid, advanced=True)

    # Take n items from it and only fetch the song/depth from each item
    return islice(((vertex['song'], depth) for vertex, depth, _ in breadth_first), n)


def recomnendations_from_song_sorted(graph, song, n=10):
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
            if n is 0:
                return
            n -= 1


def find_connections(graph, song_a, song_b):
    # Function that returns the uid of the neighbors and the song itself in sorted order
    star = lambda song: chain([song.uid], (s.uid for s in song.neigbors()))

    # Get the edges between the stars of song_a and song_b:
    edges = graph.es.select(_between=(star(song_a), star(song_b)))

    # Now find the corresponding songs again:
    for edge in edges:
        yield g.vs[edge.source], g.vs[edge.target]
