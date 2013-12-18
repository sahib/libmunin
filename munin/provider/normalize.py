#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Providers that know how to normalize specific input patterns like Artist names,
Album strings or Songtitles.

Reference
---------
"""


# Stdlib:
import re
import unicodedata


# Internal:
from munin.provider import Provider


def normalize_unicode_glyphs(string):
    return unicodedata.normalize('NFKC', string)


class NormalizeProvider(Provider):
    """Very simple provider that normalizes input strings.

    Returns a tuple with a single normalized string in it.

    **Usage example:**

        >>> provider = NormalizeProvider()
        >>> provider.do_process('    aBc  ')
        ('abc', )

    Additionaly unicode glyphs are normalized with the NFKC method.
    """
    def do_process(self, input_string):
        return normalize_unicode_glyphs(input_string.lower().strip())


class ArtistNormalizeProvider(Provider):
    """Normalize an Artist Name by normalizing common patterns.

    Takes a single string, outputs a iterable of subartists

    **Usage example:**

    .. code-block:: python

        >>> provider = ArtistNormalizeProvider()
        >>> provider.do_process('BertaX & Gustl')
        ('bertax', 'gustl')
        >>> provider.do_process("A Diablo's Swing Orchästra")
        ('diablo swing orchästra')
        >>> provider.do_process('a feat. b')
        ('a', 'b')
        >>> provider.do_process('The Beatles')
        ('beatles', )

    This provider loosely follows this convention:

        http://labrosa.ee.columbia.edu/projects/musicsim/normalization.html
    """
    def __init__(self, **kwargs):
        Provider.__init__(self, **kwargs)
        self._punctuation = re.compile("\W|_")
        self._split_reasons = frozenset(['feat', 'featuring', 'and'])
        self._strip_patterns = [re.compile(pattern) for pattern in [
            r'^the\s*', r'^a\s*', r'\s*of\s*'
        ]]

    def do_process(self, input_string):
        step = [s for s in self._punctuation.split(input_string.lower()) if s]

        sub_artists = []
        for idx, element in enumerate(step):
            if element in self._split_reasons:
                # Only handle one.
                sub_artists = [
                    ' '.join(step[:idx]),
                    ' '.join(step[idx + 1:])
                ]
                break
        else:
            sub_artists = [' '.join(step)]

        for idx, sub_artist in enumerate(sub_artists):
            for pattern in self._strip_patterns:
                sub_artists[idx] = pattern.sub('', sub_artists[idx])

        return tuple(normalize_unicode_glyphs(s.strip()) for s in sub_artists)


class AlbumNormalizeProvider(Provider):
    """Normalize an Album name by normalizing common patterns.

    Takes a single string, outputs a tuple with one normalized name in it.

    **Usage example:**

    .. code-block:: python

        >>> provider = ArtistNormalizeProvider()
        >>> provider.do_process('## The Art of getting bugs (live) CD 12')
        ('the art of getting bugs', )

    This provider loosely follows this convention:

        http://labrosa.ee.columbia.edu/projects/musicsim/normalization.html
    """
    def __init__(self, **kwargs):
        Provider.__init__(self, **kwargs)
        self._punctuation = re.compile("\W|_")
        self._strip_patterns = [re.compile(pattern) for pattern in [
            r'\s*[\(\[{].*?[}\)\]]',  # Strip everything in brackets ([{
            r'\s*cd\s*\d+'         # remove CD <X> stuff.
        ]]

    def do_process(self, input_string):
        step = input_string.lower()
        for pattern in self._strip_patterns:
            step = pattern.sub('', step)

        step = ' '.join(filter(None, self._punctuation.split(step)))
        return (normalize_unicode_glyphs(step.strip()), )


# For now they do the same:
TitleNormalizeProvider = AlbumNormalizeProvider


if __name__ == '__main__':
    import unittest
    import sys

    if '--cli' in sys.argv:
        prov = ArtistNormalizeProvider()
        print(prov.do_process(sys.argv[2]))
    else:
        class TestArtistNormalizeProvider(unittest.TestCase):
            def test_splitting(self):
                prov = ArtistNormalizeProvider()
                self.assertEqual(
                    prov.do_process('The *** Hello and Berta ###'),
                    ('hello', 'berta')
                )
                self.assertEqual(
                    prov.do_process('The *** Hello Berta ### featuring Gustl'),
                    ('hello berta', 'gustl')
                )

        class TestAlbumNormalizeProvider(unittest.TestCase):
            def test_splitting(self):
                prov = AlbumNormalizeProvider()
                self.assertEqual(
                    prov.do_process('### The art of getting &bugs (live!) [liver!!] {livest!!!} CD1'),
                    ('the art of getting bugs', )
                )

        unittest.main()
