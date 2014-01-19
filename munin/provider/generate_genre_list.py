#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
import os
import re
import pickle
import json

from urllib.request import urlopen
from urllib.parse import urlencode

# Internal:
from munin.session import get_cache_path


ECHONEST_API_KEY = 'ZSIUEIVVZGJVJVWIS'
ECHONEST_API_URL = '\
http://developer.echonest.com/api/v4/artist/list_genres?\
api_key={apikey}&format=json\
'


def load_genrelist_from_echonest(dump_path):
    """Try yo load a list of genres from echonest (with libglyr's APIKEY)

    This requires a working internet connection obviously.

    :param dump_path: Pickle the list under this path.
    :type dump_path: string
    :returns: a list with ~700 genres.
    """
    try:
        with open(dump_path, 'rb') as f:
            return pickle.load(f)
    except OSError:
        url = ECHONEST_API_URL.format(apikey=ECHONEST_API_KEY)
        json_file = json.loads(urlopen(url).read().decode('utf-8'))
        genres = {pair['name'] for pair in json_file['response']['genres']}

        # Pickle the list if desired:
        if dump_path is not None:
            with open(dump_path, 'wb') as f:
                pickle.dump(genres, f)
        return genres


# Code for wikipedia was shamelessly taken from beets:
# https://gist.github.com/sampsyo/1241307
# Adjustments were made to fix style warnings and to make it work for python3.


PAGES = [
    "List of popular music genres",
    "List of styles of music: A\u2013F",
    "List of styles of music: G\u2013M",
    "List of styles of music: N\u2013R",
    "List of styles of music: S\u2013Z"
]


BASE_URL = "http://en.wikipedia.org/w/index.php"
START_PAT = re.compile('==.*==', re.M)
END_STRING = '==References=='
ITEM_PAT = re.compile('\[\[(?:[^\]\|]*\|)?([^\]\|]*)\]\]')
BAD_NAME_PAT = re.compile('^[A-Z][a-z]?(-[A-Z][a-z]?)?$')  # Letter ranges.
INTERNAL_LINK_PAT = re.compile('[a-z][a-z]:')
DROP_PART_PAT = re.compile('\(.*\)$')


def wiki_get_page(name):
    name = name.replace(' ', '_').encode('utf8')
    params = {
        'title': name,
        'action': 'raw',
    }

    url = "{}?{}".format(BASE_URL, urlencode(params))
    return urlopen(url).read().decode('utf8')


def wiki_is_bad_name(name):
    if name.startswith('Section'):
        return True

    if BAD_NAME_PAT.match(name):
        return True

    if INTERNAL_LINK_PAT.match(name):
        return True


def wiki_genres_for(page):
    text = wiki_get_page(page)

    # Strip off top and bottom cruft.
    if END_STRING in text:
        text, _ = text.split(END_STRING, maxsplit=1)

    parts = START_PAT.split(text, maxsplit=1)
    if len(parts) is 2:
        text = parts[1]

    for line in text.splitlines():
        match = ITEM_PAT.search(line)
        if match:
            name = match.group(1)
            # Filter some non-genre links.
            if wiki_is_bad_name(name):
                continue

            yield DROP_PART_PAT.sub('', name).strip().lower()


def load_genrelist_from_wikipedia(dump_path):
    """Scrape several wikipedia pages to get genres.
    """
    try:
        with open(dump_path, 'rb') as handle:
            return pickle.load(handle)
    except OSError:
        genres = set()
        for page in PAGES:
            genres.update(filter(None, wiki_genres_for(page)))

        # Pickle the list if desired:
        if dump_path is not None:
            with open(dump_path, 'wb') as handle:
                pickle.dump(genres, handle)

        return genres


def load_genrelist():
    """Load a genre list from both wikipedia and echonest (merge them).

    If there's a 'genre.list' file in the same directory as this script
    it gets loaded, otherwise a live search is performed and the result
    gets written to 'genre.list'.
    """
    relative_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'genre.list'
    )

    try:
        with open(relative_path, 'r') as handle:
            genres = []
            for genre in handle:
                genres.append(genre.strip())
            return genres
    except OSError:
        pass

    wiki_genres = load_genrelist_from_wikipedia(
        get_cache_path('genre_list_wikipedia.dump')
    )
    echo_genres = load_genrelist_from_echonest(
        get_cache_path('genre_list_echonest.dump')
    )

    # Merge and sort them.
    genres = sorted(wiki_genres | echo_genres)

    # Pickle the list if desired:
    try:
        with open(relative_path, 'w') as handle:
            for genre in genres:
                handle.write(genre.strip() + '\n')
    except OSError:
        pass
    return genres


if __name__ == '__main__':
    for genre in load_genrelist():
        print(genre)
