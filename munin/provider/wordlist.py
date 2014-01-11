#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Providers that are table to a take a text and deliver a list of words from it.
In the simplest case this is a Tokenizer, in the more complex case
stop words are filtered and other words are normalized.

Reference
---------
"""

# Internal:
from munin.provider import Provider


class WordlistProvider(Provider):
    """
    Split the input value using the standard split function.

    **Takes:** Either a list of length one, or a single str.
    """
    def do_process(self, input_value):
        if isinstance(input_value, tuple):
            input_value = input_value[0]
        return tuple(frozenset(input_value.split()))


if __name__ == '__main__':
    import unittest

    class TestWordlistProvider(unittest.TestCase):
        def test_splitting(self):
            prov = WordlistProvider()
            print(prov.do_process('Hello Berta'))

    unittest.main()
