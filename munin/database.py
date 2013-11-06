#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from contextlib import contextmanager
from itertools import combinations
from collections import Counter

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
        visual_style["vertex_label"] = self._graph.vs["name"]
        visual_style["bbox"] = (300, 300)
        visual_style["margin"] = 20
        # visual_style["edge_width"] = [1 + 2 * int(is_formal) for is_formal in g.es["is_formal"]]
        # visual_style["layout"] = self._graph.layout('kk'),
        # visual_style["vertex_color"] = [color_dict[gender] for gender in g.vs["gender"]]
        igraph.plot(self._graph, **visual_style)

    def find_common_attributes(self):
        counter = Counter()
        for song in self._song_list:
            counter.update(song.keys())
        print(counter.most_common())

    def sample_max_confidence(self):
        step_divisor = 100
        if len(self._song_list) < 1000:
            step_divisor = 10
        elif len(self._song_list) < 100:
            step_divisor = 1

        average_confidence = 0
        for song in self._song_list[::max(0, len(self._song_list) // step_divisor)]:
            _, confidence = song.confidence

    def rebuild(self):
        '''Rebuild all distances and the associated graph.

        This will be triggered for you automatically after a transaction.
        '''
        self._graph = igraph.Graph()
        self.find_common_attributes()

        # Add N vertices to the graph
        # self._graph.add_vertices(len(self._song_list))
        # for idx, song in enumerate(self._song_list):
        #    self._graph.add_vertex(name=str(idx), song=song)
        for song in self._song_list:
            song.calculate_confidence()

        MAX_DIFF = 1.0 * self._session.mask_length

        def heuristic(song_a, song_b):
            filled_a, confidence_a = song_a.confidence
            filled_b, confidence_b = song_b.confidence

            # print(filled_a, confidence_a, filled_b, confidence_b)
            if abs(filled_a - filled_b) > 0.5:
                return False

            diff = sum(
                abs(a - b) for a, b in zip(confidence_a, confidence_b)
                if a is not None and b is not None
            )
            # print('Diff', diff)
            if diff > MAX_DIFF:
                return False

            return True

        print()

        total = len(self._song_list)
        total = total * total / 2
        idx = 0
        compares = 0

        for song_a, song_b in combinations(self._song_list, 2):
            # print(song_a, song_b)
            if heuristic(song_a, song_b):
                # Compute a Distane object:
                distance = song_a.distance_compute(song_b)

                # Adding works bidirectional:
                song_a.distance_add(song_b, distance)

                # Add it to the graph
                #self._graph.add_edge(song_a.uid, song_b.uid, dist=distance, weight=distance.distance)
                # print(idx / total * 100, '%                ', end='\r')

                compares += 1

            idx += 1
        print('In total', compares, idx, compares / idx * 100, '                      ')
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
                N = 200
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

    #  unittest.main()
    # DatabaseTests().test_basic()
    def main():
        from munin.distance import DistanceFunction

        class _DummyDistance(DistanceFunction):
            def compute_confidence(self, value_list):
                return value_list[0]

        dprov = _DummyProvider()
        dfunc = _DummyDistance(dprov)
        session = Session('session_test', {
            'genre': (dprov, dfunc, 0.2),
            'artist': (dprov, dfunc, 0.3)
        }, path='/tmp')

        with session.database.transaction():
            N = 500
            for i in range(int(N / 2) + 1):
                session.database.add_values({
                    'genre': i / N,
                    'artist': 1.0 - i / N
                })
                session.database.add_values({
                    'genre': 1.0 - i / N,
                    'artist': i / N
                })
    unittest.main()
    # main()
