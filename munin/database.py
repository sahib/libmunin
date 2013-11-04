#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from contextlib import contextmanager
from itertools import combinations

# Internal:
from munin.song import Song

# External:
import igraph


class Database:
    'Class managing Database concerns.'
    def __init__(self, session):
        '''Usually you access this as ``.database`` attribute of
        :class:`munin.session.Session`.

        You can do the following tasks with it:

        * Add songs to the database (:func:`add`, :func:`add_values`)
        * Trigger updates (:func:`rebuild`, :func:`transaction`)
        * Iterative over the database (``for song in database``).
        * Get a song by it's uid. (``database[song.uid]``)

        .. note::

            The division of :class:`munin.session.Session` and :class:`Database`
            is purely cosmetical. Both classes cannot exist on its own.
        '''
        self._session = session
        self._song_list = []
        self._graph = igraph.Graph()

    def __iter__(self):
        return iter(self._song_list)

    def __getitem__(self, idx):
        return self._song_list[idx]

    def plot(self):
        visual_style = {}
        visual_style["vertex_size"] = 20
        # visual_style["vertex_color"] = [color_dict[gender] for gender in g.vs["gender"]]
        visual_style["vertex_label"] = self._graph.vs["name"]
        # visual_style["edge_width"] = [1 + 2 * int(is_formal) for is_formal in g.es["is_formal"]]
        # visual_style["layout"] = self._graph.layout('kk'),
        visual_style["bbox"] = (300, 300)
        visual_style["margin"] = 20
        igraph.plot(self._graph, **visual_style)

    def rebuild(self):
        '''Rebuild all distances and the associated graph.

        This will be triggered for you automatically after a transaction.
        '''
        self._graph = igraph.Graph()

        # Add N vertices to the graph
        # self._graph.add_vertices(len(self._song_list))
        for idx, song in enumerate(self._song_list):
            self._graph.add_vertex(name=str(idx), song=song)

        # TODO: All edges get added, which is silly.

        for song_a, song_b in combinations(self._song_list, 2):
            # Compute a Distane object:
            distance = song_a.distance_compute(song_b)

            # Adding works bidirectional:
            song_a.distance_add(song_b, distance)

            # Add it to the graph
            self._graph.add_edge(song_a.uid, song_b.uid, dist=distance, weight=distance.distance)

        # print('plotting')
        # self.plot()

    def add_song(self, song):
        '''Add a single song to the database.

        :returns: the added song for convinience.
        '''
        if song is not None:
            song.uid = len(self._song_list)
            self._song_list.append(song)

        return song

    def add_values(self, value_dict):
        '''Creates a song from value dict and add it to the database.

        .. seealso:: :func:`add`

        The song will be configured to the config values set in the Session.

        :returns: the added song for convinience
        '''
        for key, value in value_dict.items():
            try:
                provider = self._session.provider_for_key(key)
                value_dict[key] = provider.process(value)
            except KeyError:
                raise KeyError('key "{k}" is not in attribute mask'.format(k=key))

        return self.add_song(Song(
            self._session, value_dict,
            max_neighbors=self._session.config['max_neighbors'],
            max_distance=self._session.config['max_distance']
        ))

    @contextmanager
    def transaction(self):
        'Convienience method: Excecute block and call :func:`rebuild` afterwards.'
        yield
        self.rebuild()


if __name__ == '__main__':
    import unittest
    from munin.session import Session
    from munin.provider import DirectProvider

    class _DummyProvider(DirectProvider):
        def __init__(self):
            DirectProvider.__init__(self, 'dummy', is_reversible=False)

        def process(self, input_value):
            return (input_value, )

    class DatabaseTests(unittest.TestCase):
        def setUp(self):
            self._session = Session('session_test', {
                'genre': (_DummyProvider(), None, 0.2),
                'artist': (_DummyProvider(), None, 0.3)
            }, path='/tmp')

        def test_basics(self):
            with self._session.database.transaction():
                N = 20
                for i in range(N):
                    self._session.database.add_values({
                        'genre': i / N,
                        'artist': i / N
                    })
                    # self._session.database.add_values({
                    #     'genre': 'alfonso',
                    #     'artist': ''
                    # })

            # song_a, song_b = self._session.database
            # self.assertAlmostEqual(song_a.distance_get(song_b).distance, 0.0)
            # self.assertAlmostEqual(song_b.distance_get(song_b).distance, 0.0)

        def test_no_match(self):
            with self.assertRaisesRegex(KeyError, '.*attribute mask.*'):
                self._session.database.add_values({
                    'not_in_session': 42
                })

    unittest.main()
