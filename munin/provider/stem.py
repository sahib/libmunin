'''
.. currentmodule:: munin.provider.stem

Overview
--------

Providers that stems it's input by various algorithms.
By their nature they are not reversible.

If input value is a string a list with one string is returned,
if it is an iterable, all elements in this iterable will be stemmed.

**Usage Example:** ::

    >>> p = LancasterStemProvider()
    >>> p.process(['Fish', 'fisher', 'fishing'])  # Either a list of words...
    ['fish', 'fish', 'fish']
    >>> p.process('stemming') # Or a single word.
    'stem'

Reference
---------
'''

from munin.provider import Provider
from collections import Iterable


class _BaseStemProvider(Provider):
    def process(self, input_value):
        if isinstance(input_value, str):
            return [self._stem(input_value)]
        else:
            return [self._stem(word) for word in input_value]


class LancasterStemProvider(_BaseStemProvider):
    'Stem the input values (either a single word or a list of words)'
    def __init__(self, compress=False):
        '''This Provider takes no options.

        .. note:: LancasterStemmer is known to be more aggressive than PorterStemmer.
        '''
        Provider.__init__(self, compress=compress)

        from nltk.stem import LancasterStemmer
        self._stemmer = LancasterStemmer()
        self._stem = lambda word: self._stemmer.stem(word)


class SnowballStemProvider(_BaseStemProvider):
    '''Stem the input value by the Snowball Stemming Algorithm
    *("PorterStemmer with languages")*
    '''
    def __init__(self, language='english', compress=False):
        '''
        See here for a full list of languages:

            http://nltk.org/_modules/nltk/stem/snowball.html


        :param language: the language for the algorithm to use.
        :type language: str
        '''
        Provider.__init__(self, compress=compress)

        from nltk.stem import SnowballStemmer
        self._stemmer = SnowballStemmer(language)
        self._stem = lambda word: self._stemmer.stem(word)


if __name__ == '__main__':
    import unittest

    class StemProviderTests(unittest.TestCase):
        def test_valid(self):
            for prov in [LancasterStemProvider(), SnowballStemProvider()]:
                words = ['Fish', 'fisher', 'fishing']
                # words = ['heaven', 'beatles', 'beatle']
                print(prov)
                print([prov.process(word) for word in words])
                print(prov.process(words))

    # Disabled for now, since we'd need to import it on TravisCI
    # and the PyPi package simply does not work for Py3.
    unittest.main()
