#!/usr/bin/env python
# encoding: utf-8

"""
Overview
~~~~~~~~

Interface for loading stopwords from a set of 12 languages that
are packaged along libmunin.

The stopwords can be used to split text into important and unimportant words.
Additionally text language can be guessed through the ``guess_language`` module.

Reference
~~~~~~~~~
"""


import os
import pkgutil


__path__ = os.path.dirname(pkgutil.extend_path(__file__, __name__))


# Cache all already loaded stopwords, since loading them takes a tad longer.
STOPWORD_CACHE = {}


def parse_stopwords(handle):
    """Parse a file with stopwords in it into a list of stopwords.

    :param handle: an readable file handle.
    :returns: An iterator that will yield stopwords.
    """
    for line in handle:
        yield line.strip().lower()


def load_stopwords(language_code):
    """Load a stopwordlist from the data directory.

    Returns a frozenset with all stopwords or an empty set if
    the language_code was not recognized.

    :param language_code: A ISO-639 Alpha2 language code
    :returns: A frozenset of words.
    """
    global STOPWORD_CACHE
    if language_code in STOPWORD_CACHE:
        return STOPWORD_CACHE[language_code]

    relative_path = os.path.join(__path__, 'data', language_code)
    try:
        with open(relative_path, 'r') as handle:
            stopwords = frozenset(parse_stopwords(handle))
            STOPWORD_CACHE[language_code] = stopwords
            return stopwords
    except OSError:
        return frozenset([])


if __name__ == '__main__':
    import sys
    import guess_language

    if '--cli' in sys.argv:
        code = guess_language.guess_language(sys.argv[2])
        print(load_stopwords(code))
