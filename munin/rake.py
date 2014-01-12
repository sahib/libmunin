#!/usr/bin/env python
# encoding: utf-8

"""
Overview
~~~~~~~~

This module contains code for automatic keywordextraction.

The algorithm used is RAKE (Rapid Automatic Keyword Extraction) as described in:

    Rose, S., D. Engel, N. Cramer, and W. Cowley (2010).
    Automatic keyword extraction from indi-vidual documents.
    Text Mining: Applications and Theory

The original code is based on aneesha's Python implemenation of RAKE,
but has been extended with automatic stopwordlist retrieval and stemming:

    https://github.com/aneesha/RAKE

While adding these features all code was rewritten.


.. note::

    Of all functions below, you'll probably only need :func:`extract_keywords`.

Reference
~~~~~~~~~
"""

# Stdlib:
import re
import operator

from collections import deque, Counter, OrderedDict
from itertools import combinations


# Internal:
import munin.stopwords


# External:
import Stemmer
import guess_language
guess_language.use_enchant(True)


# This is a fallback for the case when no stemmer for a language was found:
class DummyStemmer:
    """Stemmer class that does not modify it's input"""
    def stemWord(self, word):
        return word


def separate_words(text):
    """Separate a text (or rather sentece) into words

    Every non-alphanumeric character except + - / is considered as word-delim.
    Words that look like numbers are ignored too.

    :returns: an iterable of words.
    """
    words = deque()
    for word in filter(None, re.split('[^\w+-/]', text)):
        word = word.strip().lower()
        # Leave numbers in the phrase, but do not count them as words.
        try:
            float(word)
        except ValueError:
            words.append(word)
    return words


def split_sentences(text):
    """Split a text into individual sentences.

    Newline is not considererd to be a new sentence.

    :returns: an iterable of strings.
    """
    return re.split('[.!?,;:\t\\-\\"\\(\\)\\\'\u2019\u2013]', text)


def phrase_iter(sentence, stopwords, stemmer):
    """Splits a sentence into phrases (sequece of stopwordfree words).

    :param sentence: The sentece to split into phrases.
    :param stopwords: A set of stopwords/
    :param stemmer: A stemmer class to be used (language aware)
    :rtype: [str]
    :returns: An iterator that yields a list of words.
    """
    def yield_result(phrase):
        if phrase:
            yield [stemmer.stemWord(word) for word in phrase]

    phrase = deque()
    for word in separate_words(sentence):
        if word in stopwords:
            yield_result()
            phrase = deque()
            continue
        phrase.append(word)
    yield_result()


def extract_phrases(sentences, language_code, use_stemmer):
    """Extract the phrases from all sentences.

    A phrase is a sequence of words that do not contain a stopword.

    :param sentences: An iterable of sentences (str)
    :param language_code: an ISO 639 language code
    :param use_stemmer: If True words in the phrases are also stemmed.
    :returnes: An iterable of phrases. (str)
    """
    stopwords = munin.stopwords.load_stopwords(language_code)

    # If we have no stopwordlist for that, we can't do much:
    if not stopwords:
        return None

    try:
        if use_stemmer:
            language_stemmer = Stemmer.Stemmer(language_code)
        else:
            language_stemmer = DummyStemmer()
    except KeyError:
        # effectively disable stemming:
        language_stemmer = DummyStemmer()

    phrases = deque()
    for sentence in sentences:
        phrases += phrase_iter(sentence.strip(), stopwords, language_stemmer)
    return phrases


def word_scores(phrases):
    """Calculate the scores of each individual word, depending on the phrase length.

    :param phrases: An iterable of phrases
    :returns: A mapping from a word to it's score (degree(w) / freq(w))
    """
    freqs, degrees = Counter(), Counter()

    for phrase in phrases:
        degree = len(phrase) - 1
        for word in phrase:
            freqs[word] += 1
            degrees[word] += degree

    # Calculate Word scores = deg(w) / freq(w)
    return {word: (degrees[word] + freq) / freq for word, freq in freqs.items()}


def candidate_keywordscores(phrases, wordscore):
    """Generate the actual results dictionary out of the phrases and wordscore.

    :param phrases: by :func:`extract_phrases`
    :param wordscore: by :func:`word_scores`
    :returns: a mapping of keyword_sets to their rating
    """
    candidates = {}
    for phrase in phrases:
        candidates[frozenset(phrase)] = sum(wordscore[word] for word in phrase)

    return OrderedDict(sorted(
        candidates.items(),
        key=operator.itemgetter(1),
        reverse=True
    ))


def filter_subsets(keywords):
    """Remove keywordsets that are a subset of larger sets.

    This modifies it's input, but returns it for convinience.

    :returns: keywords, the modified input.
    """
    to_delete = deque()
    for set_a, set_b in combinations(keywords.keys(), 2):
        if set_a.issubset(set_b):
            to_delete.append(set_a)
        elif set_b.issubset(set_a):
            to_delete.append(set_b)

    for sub_keywords in set(to_delete):
        del keywords[sub_keywords]

    return keywords


def extract_keywords(text, use_stemmer=True):
    """Extract the keywords from a certain text.

    :param use_stemmer: If True a Snowball Stemmer will be used for all words.
    :returns: A sorted mapping between a set of keywords and their rating.
    :rtype: :class:`collections.OrderedDict`
    """
    language_code = guess_language.guess_language(text)
    phrases = extract_phrases(split_sentences(text), language_code, use_stemmer)

    # This can happen if no stopwords are avaible, or a one-word input was used.
    if phrases is None:
        return None, OrderedDict()

    scores = word_scores(phrases)
    keywords = candidate_keywordscores(phrases, scores)
    return language_code, filter_subsets(keywords)


###########################################################################
#                       Test Main (read from stdin)                       #
###########################################################################

if __name__ == '__main__':
    import sys
    text = sys.stdin.read()

    use_stemmer = True
    if '--no-stemmer' in sys.argv:
        use_stemmer = False

    lang, keywords_map = extract_keywords(text, use_stemmer=use_stemmer)
    for keywords, rating in keywords_map.items():
        print('{:>7.3f}: {}'.format(rating, keywords))
