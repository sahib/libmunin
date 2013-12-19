#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Interface for loading stopwords from a set of 12 languages that
are packaged along libmunin.

The stopwords can be used to split text into important and unimportant words.
Additionally text language can be guessed through the ``guess_language`` module.

Reference
---------
"""


import os
import pkgutil
import guess_language


__path__ = os.path.dirname(pkgutil.extend_path(__file__, __name__))


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
    relative_path = os.path.join(__path__, language_code)
    try:
        with open(relative_path, 'r') as handle:
            return frozenset(parse_stopwords(handle))
    except OSError:
        return frozenset([])


def stopwords_for_text(text):
    """Load a fitting stopwords list for a certain text. Try to autorecognize
    the language.

    .. note::

        If you are searching for a function that finds the text's language
        use this:

        .. code-block:: python

            >>> import guess_language
            >>> guess_language.guess_language(
                    "je suis avec michael et christophe dans la chat"
            )
            'fr'

    This is based on the guess_language-spirit package.

    :param text: an arbitary text to guess the language from.
                 Should be more than 20 characters.
    :returns: A frozenset of stopwords or an empty frozenset.
    """
    code = guess_language.guess_language(text)
    return load_stopwords(code)


if __name__ == '__main__':
    import sys
    if '--cli' in sys.argv:
        print(stopwords_for_text(sys.argv[2]))
