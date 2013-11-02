#!/usr/bin/env python
# encoding: utf-8

from contextlib import contextmanager
from itertools import combinations


class Database:
    'Class managing Database concerns.'
    def __init__(self, session):
        '''Usually you access this as ``.database`` attribute of
        :class:`munin.session.Session`.

        You can do the followin tasks with it:

        * Add songs to the database (:func:`add`, :func:`add_values`)
        * Trigger updates (:func:`rebuild`, :func:`transaction`)

        .. note::

            The division of :class:`munin.session.Session` and :class:`Database`
            is purely cosmetical. Both classes cannot exist on its own.
        '''
        self._session = session
        self._song_list = []

    def rebuild(self):
        '''Rebuild all distances and the associated graph.

        This will be triggered for you automatically after a transaction.
        '''
        for song_a, song_b in combinations(self._song_list):
            # Compute a Distane object:
            distance = song_a.distance_compute(song_b)

            # Adding works bidirectional:
            song_a.distance_add(song_b, distance)

    def add(self, song):
        '''Add a single song to the database.

        :returns: the added song for convinience.
        '''
        if song is not None:
            self._song_list.append(song)

        return song

    def add_values(self, value_dict):
        '''Creates a song from value dict and add it to the database.

        .. seealso:: :func:`add`

        The song will be configured to the config values set in the Session.

        :returns: the added song for convinience
        '''
        self.add(Song(
            self._session, value_dict,
            neighbors=self._session.config['max_neighbors'],
            max_distance=self._session.config['max_distance']
        ))

    @contextmanager
    def transaction(self):
        'Convienience method: Excecute block and call :func:`rebuild` afterwards.'
        yield
        self.rebuild()


if __name__ == '__main__':
    import unittest

    # TODO: Stub.
    class DatabaseTests(unittest.TestCase):
        def test_basic_attributes(self):
            pass

    unittest.main()
