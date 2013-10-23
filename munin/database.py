#!/usr/bin/env python
# encoding: utf-8

from contextlib import contextmanager


class Database:
    def __init__(self, session):
        self._session = session
        self._song_list = []
        self._transaction = False

    def rebuild(self):
        pass

    def add(self, song):
        if song is not None:
            self._song_list.append(song)

    @contextmanager
    def transaction(self):
        self._transaction = True


if __name__ == '__main__':
    import unittest

    class DatabaseTests(unittest.TestCase):
        def test_basic_attributes(self):
            pass

    unittest.main()
