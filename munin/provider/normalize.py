#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
import re
import unicodedata


# Internal:
from munin.provider import Provider


def normalize_unicode_glyphs(string):
    return unicodedata.normalize('NFKC', string)


class ArtistNormalizeProvider(Provider):
    """Normalize an Artist Name by normalizing common patterns.

    Takes a single string.

    This provider loosely follows this convention:

        http://labrosa.ee.columbia.edu/projects/musicsim/normalization.html
    """
    def __init__(self, **kwargs):
        Provider.__init__(self, **kwargs)
        self._punctuation = re.compile("\W|_")
        self._split_reasons = frozenset(['feat', 'featuring', '&', 'and'])
        self._strip_patterns = [re.compile(pattern) for pattern in [
            '^the\s*', '^a\s*', '\s*of\s*'
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
                sub_artists[idx] = pattern.sub('', sub_artist)

        return tuple(normalize_unicode_glyphs(s) for s in sub_artists)


# TODO: TitleNormalizer, AlbumNormalizer


if __name__ == '__main__':
    import unittest

    class TestArtistNormalizeProvider(unittest.TestCase):
        def test_splitting(self):
            prov = ArtistNormalizeProvider()
            print(prov.do_process('The *** Hello & Berta ###'))
            print(prov.do_process('The *** Hello & Berta ### featuring Gustl'))

    unittest.main()
