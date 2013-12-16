#!/usr/bin/env python
# encoding: utf-8

from colorsys import hsv_to_rgb
from collections import deque


def _build_graph_from_song_list(graph, song_list):
    for song in song_list:
        graph.add_vertex(song=song)

    # Gather all edges in one container
    # (this speeds up adding edges)
    edge_set = deque()
    for song_a in song_list:
        for song_b, _ in song_a.distance_iter():
            # Make Edge Deduplication work:
            if song_a.uid < song_b.uid:
                edge_set.append((song_b.uid, song_a.uid))
            else:
                edge_set.append((song_a.uid, song_b.uid))

    # Filter duplicate edge pairs.
    graph.add_edges(set(edge_set))


def _color_from_distance(distance):
    return '#' + '01234567890ABCDEF'[int(distance * 16)] * 2 + '0000'


def _edge_color_list(graph):
    edge_colors, edge_widths = deque(), deque()

    for edge in graph.es:
        a, b = graph.vs[edge.source]['song'], graph.vs[edge.target]['song']
        distance = a.distance_get(b)
        if distance is not None:
            edge_colors.append(_color_from_distance(distance.distance))
            edge_widths.append((distance.distance + 0.1) * 3)

    return list(edge_colors), list(edge_widths)


def _style(graph, width, height):
    colors = graph.eigenvector_centrality(directed=False)
    edge_color, edge_width = _edge_color_list(graph)
    return {
        'vertex_label': [str(vx['song'].uid) for vx in graph.vs],
        'edge_color': edge_color,
        'edge_width': edge_width,
        'vertex_color': [hsv_to_rgb(v, 1.0, 1.0) for v in colors],
        'vertex_label_color': [hsv_to_rgb(1 - v, 0.2, 0.1) for v in colors],
        'vertex_size': [42] * len(graph.vs),
        'layout': graph.layout('fr'),
        'bbox': (width, height)
    }


def plot(database, width=1000, height=1000):
    """Plot the current graph for debugging purpose.

    Will try to open an installed image viewer - does not return an image.

    :param database: The database (and the assoicate graph with it) to plot.
    :param width: Width of the plotted image in pixel.
    :param height: Width of the plotted image in pixel.
    """
    try:
        import igraph
    except ImportError:
        print('-- You need igraph and python-igraph installed for this.')
        return

    graph = igraph.Graph(directed=False)
    _build_graph_from_song_list(graph, database)
    style = _style(graph, width, height)
    igraph.plot(graph, **style)
