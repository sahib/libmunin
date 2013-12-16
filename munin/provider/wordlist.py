#!/usr/bin/env python
# encoding: utf-8

# Internal:
from munin.provider import Provider


# TODO: StopwordlistProvider (at least for english)

class WordlistProvider(Provider):
    def do_process(self, input_value):
        if isinstance(input_value, tuple):
            input_value = input_value[0]
        return tuple(input_value.split())


if __name__ == '__main__':
    import unittest

    class TestWordlistProvider(unittest.TestCase):
        def test_splitting(self):
            prov = WordlistProvider()
            print(prov.do_process('Hello Berta'))

    unittest.main()
