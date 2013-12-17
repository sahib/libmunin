"""
.. currentmodule:: munin.provider.stem

Overview
--------

Providers that stems it's input by various algorithms.
By their nature they are not reversible.

If input value is a string a list with one string is returned,
if it is an iterable, all elements in this iterable will be stemmed.

**Usage Example:** ::

    >>> p = StemProvider()
    >>> p.process(['Fish', 'fisher', 'fishing'])  # Either a list of words...
    ['fish', 'fish', 'fish']
    >>> p.process('stemming') # Or a single word.
    'stem'

Reference
---------
"""

from munin.provider import Provider


from Stemmer import Stemmer
STEMMER = Stemmer('english')


class StemProvider(Provider):
    """Stem the input values (either a single word or a list of words)

    Uses the porter stemmer algorithm.
    """
    def __init__(self, language='english', **kwargs):
        """
        See here for a full list of languages:

            http://nltk.org/_modules/nltk/stem/snowball.html

        .. note::

            This does not depend on nltk, it depends on the ``pystemmer`` package.

        :param language: language to use during stemming, defaults to english.
        """
        Provider.__init__(self, **kwargs)
        self._stemmer = Stemmer(language)

    def do_process(self, input_value):
        if isinstance(input_value, str):
            return self._stemmer.stemWord(input_value)
        else:
            return self._stemmer.stemWords(input_value)


if __name__ == '__main__':
    import unittest

    class StemProviderTests(unittest.TestCase):
        def test_valid(self):
            prov = StemProvider()
            words = ['Fish', 'fisher', 'fishing']
            # words = ['heaven', 'beatles', 'beatle']
            print(prov)
            print([prov.do_process(word) for word in words])
            print(prov.do_process(words))

    unittest.main()
