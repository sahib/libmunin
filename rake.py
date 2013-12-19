# Implementation of RAKE - Rapid Automtic Keyword Exraction algorithm as
# described in: Rose, S., D. Engel, N. Cramer, and W. Cowley (2010).  Automatic
# keyword extraction from indi-vidual documents.  In M. W. Berry and J. Kogan
# (Eds.), Text Mining: Applications and Theory.unknown: John Wiley and Sons,
# Ltd.

import re
import operator

from collections import deque, Counter, OrderedDict
from itertools import combinations


def isnum(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def load_stopwords(stopWordFile):
    with open(stopWordFile) as handle:
        return [word.strip() for word in handle]


def separate_words(text, minWordReturnSize):
    words = deque()
    for word in filter(None, re.split('[^\w+-/]', text)):
        word = word.strip().lower()
        #leave numbers in phrase, but don't count as words, since they tend to
        # invlate scores of their phrases
        if len(word) > minWordReturnSize and not isnum(word):
            words.append(word)
    return words


def split_sentences(text):
    # TODO: add \n for lyrics
    return re.split('[.!?,;:\n\t\\-\\"\\(\\)\\\'\u2019\u2013]', text)


def generate_candidate_keywords(sentenceList, path):
    stopwordregexlist = ['\\b' + word + '\\b' for word in load_stopwords(path)]
    stopwordpattern = re.compile('|'.join(stopwordregexlist), re.IGNORECASE)

    phrases = deque()
    for sentence in sentenceList:
        for phrase in stopwordpattern.split(sentence.strip()):
            phrase = phrase.strip().lower()
            if phrase:
                phrases.append(phrase)
    return phrases


def calculate_word_scores(phrases):
    freqs, degrees = Counter(), Counter()

    for phrase in phrases:
        words = separate_words(phrase, 0)
        degree = len(words) - 1
        for word in words:
            freqs[word] += 1
            degrees[word] += degree

    # Calculate Word scores = deg(w) / freq(w)
    score = Counter()
    for word, freq in freqs.items():
        degrees[word] = degrees[word] + freq
        score[word] = degrees[word] / freq
    return score


def generate_candidate_keywordscores(phrases, wordscore):
    candidates = Counter()
    for phrase in phrases:
        words = separate_words(phrase, 0)
        candidates[phrase] = sum(wordscore[word] for word in words)
    return candidates


def filter_subsets(keywords):
    to_delete = deque()
    for set_a, set_b in combinations(keywords.keys(), 2):
        if set_a.issubset(set_b):
            to_delete.append(set_a)
        elif set_b.issubset(set_a):
            to_delete.append(set_b)

    for sub_keywords in to_delete:
        print('deleting', sub_keywords)
        del keywords[sub_keywords]

if __name__ == '__main__':
    import sys
    text = sys.stdin.read()

    sentenceList = split_sentences(text)
    phrases = generate_candidate_keywords(sentenceList, "SmartStoplist.txt")
    wordscores = calculate_word_scores(phrases)
    candidates = generate_candidate_keywordscores(phrases, wordscores)
    sorted_keywords = sorted(
        candidates.items(),
        key=operator.itemgetter(1),
        reverse=True
    )

    keywords_map = OrderedDict()
    for idx, (keywords, rating) in enumerate(sorted_keywords):
        words = separate_words(keywords, 0)
        keywords_map[frozenset(words)] = rating

    filter_subsets(keywords_map)

    for keywords, rating in keywords_map.items():
        print('{:2.3f}: {}'.format(rating, keywords))
