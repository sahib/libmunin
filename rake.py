import re
import operator

from collections import deque, Counter, OrderedDict
from itertools import combinations


def load_stopwords(stopWordFile):
    with open(stopWordFile) as handle:
        return frozenset([word.strip() for word in handle])


def separate_words(text):
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
    return re.split('[.!?,;:\t\\-\\"\\(\\)\\\'\u2019\u2013]', text)


def phrase_iter(sentence, stopwords):
    phrase = deque()
    for word in separate_words(sentence):
        if word in stopwords:
            if phrase:
                yield phrase
            phrase = deque()
            continue
        phrase.append(word)


def extract_phrases(sentences):
    phrases = deque()

    # TODO: detect language
    stopwords = load_stopwords('SmartStoplist.txt')

    for sentence in sentences:
        phrases += phrase_iter(sentence.strip(), stopwords)
    return phrases


def word_scores(phrases):
    freqs, degrees = Counter(), Counter()

    for phrase in phrases:
        degree = len(phrase) - 1
        for word in phrase:
            freqs[word] += 1
            degrees[word] += degree

    # Calculate Word scores = deg(w) / freq(w)
    return {word: (degrees[word] + freq) / freq for word, freq in freqs.items()}


def candidate_keywordscores(phrases, wordscore):
    candidates = {}
    for phrase in phrases:
        candidates[frozenset(phrase)] = sum(wordscore[word] for word in phrase)

    return OrderedDict(sorted(
        candidates.items(),
        key=operator.itemgetter(1),
        reverse=True
    ))


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

    return keywords


def extract_keywords(text):
    sentences = split_sentences(text)
    phrases = extract_phrases(sentences)
    scores = word_scores(phrases)
    keywords = candidate_keywordscores(phrases, scores)
    return filter_subsets(keywords)


if __name__ == '__main__':
    import sys
    text = sys.stdin.read()

    keywords_map = extract_keywords(text)
    for keywords, rating in keywords_map.items():
        print('{:2.3f}: {}'.format(rating, keywords))
