#!/usr/bin/env python
# encoding: utf-8


import urllib.request as url
import pprint
import pickle
import json
import re

'''
Get a list of genre via echonest and try to make a Tree out of them:

    Genres:
        Melodic Death Metal
        Pagan Metal
        Japan Pop

    Tree:

        music
        |- Pop
          |- Japan
        |- Metal
          |- Pagan
          |- Death
             |- Melodic
'''


def load_genrelist_from_echonest(dump_path):
    URL = 'http://developer.echonest.com/api/v4/artist/list_genres?api_key=ZSIUEIVVZGJVJVWIS&format=json'
    json_file = json.loads(url.urlopen(URL).read().decode('utf-8'))
    genres = [pair['name'] for pair in json_file['response']['genres']]
    with open(dump_path, 'wb') as f:
        pickle.dump(genres, f)
    return genres


def unflatten_list(genres):
    top_set = {}
    for genre in genres:
        *rest, last = re.split('[-\s]', genre)
        first_part = ' '.join(rest)
        sub_genres = top_set.setdefault(last, set())
        if not sub_genres or first_part:
            sub_genres.add(first_part)
    return {key: set(filter(None, value)) for key, value in top_set.items()}


if __name__ == '__main__':
    # Add a caching layer:
    dump_path = '/tmp/genre.dump'
    try:
        with open(dump_path, 'rb') as f:
            genres = pickle.load(f)
    except OSError:
        genres = load_genrelist_from_echonest(dump_path)

    top_set = unflatten_list(genres)
    pprint.pprint(top_set)

    new_set = {}
    for key, value in top_set.items():
        new_sub_set = unflatten_list(filter(None, value))
        new_set[key] = new_sub_set
        for sub_key, value in new_sub_set.items():
            if len(value) > 1:
                new_set[key][sub_key] = unflatten_list(value)
    pprint.pprint(new_set)
