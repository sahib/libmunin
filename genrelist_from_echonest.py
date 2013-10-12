#!/usr/bin/env python
# encoding: utf-8

import urllib.request
import pickle
import json
import re

from stemming.porter2 import stem

'''
Get a list of genre via echonest and try to make a Tree out of them:

    Genres:
        Melodic Death Metal
        Pagan Metal
        Japan Pop

    Tree:

        music
        |- pop
          |- japan
        |- metal
          |- pagan
          |- death
             |- melodic
'''


def load_genrelist_from_echonest(dump_path):
    URL = 'http://developer.echonest.com/api/v4/artist/list_genres?api_key=ZSIUEIVVZGJVJVWIS&format=json'
    json_file = json.loads(urllib.request.urlopen(URL).read().decode('utf-8'))
    genres = [pair['name'] for pair in json_file['response']['genres']]
    with open(dump_path, 'wb') as f:
        pickle.dump(genres, f)
    return genres


class Tree:
    def __init__(self, genre, children=None, parent=None):
        self.genre = genre
        self.children, self.parent = children or [], parent
        self._index = {}

    def build_index_recursively(self):
        for idx, child in enumerate(self.children):
            self._index[stem(child.genre)] = idx
            child.build_index_recursively()

    def add(self, child):
        self.children.append(child)

    def remove(self, child):
        self.children.remove(child)

    def find_linear(self, genre):
        for child in self.children:
            if child.genre == genre:
                return child

    def find(self, genre):
        pos = self._index.get(genre)
        if pos is not None:
            return self.children[pos]

    def print(self, _tabs=1):
        print('    ' * _tabs, self.genre, stem(self.genre).join(('[', ']')))

        for child in self.children:
            child.print(_tabs=_tabs + 1)


def unflatten_list(root):
    top_set = {}
    was_flattened = False

    for child in root.children:
        genre = child.genre
        *rest, last = re.split('[-\s]', genre)
        if rest:
            was_flattened = True

        first_part = ' '.join(rest)
        sub_genres = top_set.setdefault(last, set())
        if not sub_genres or first_part:
            sub_genres.add(first_part)

    root.children = []
    for genre, sub_genres in top_set.items():
        root.add(Tree(genre, children=[Tree(g) for g in sub_genres if g]))
        for child in root.children:
            child.parent = root
            for grandchild in child.children:
                grandchild.parent = child
    return was_flattened


def recursive_unflatten(root):
    if unflatten_list(root):
        for child in root.children:
            recursive_unflatten(child)


def build_genre_tree():
    # Add a caching layer:
    dump_path = '/tmp/genre.dump'
    try:
        with open(dump_path, 'rb') as f:
            genres = pickle.load(f)
    except OSError:
        genres = load_genrelist_from_echonest(dump_path)

    root = Tree('music', children=[Tree(genre) for genre in genres])
    recursive_unflatten(root)

    # Manual corrections:
    # Fix the 'music' Node:
    # Just pull all subgenres on layer up.
    music_node = root.find_linear('music')
    for child in music_node.children:
        root.add(child)
    root.remove(music_node)

    # Fix the core genres manually to be a subgenre of 'core'
    core_node = root.find_linear('core')

    to_delete = []
    for child in root.children:
        if 'core' in child.genre and child.genre != 'core':
            actual_name, _ = child.genre.split('core')
            core_node.add(Tree(actual_name, parent=core_node))
            to_delete.append(child)

    for child in to_delete:
        root.remove(child)

    # 'death core' was somehow there as 'deathcore' too:
    core_node.remove(core_node.find_linear('death'))

    # Add some common not already in:
    for to_add in ['vocal', 'speech']:
        root.add(Tree(to_add, parent=root))

    root.build_index_recursively()
    return root


def prepare_single_genre(genre):
    return list(filter(
        lambda elem: elem != '-',
        [stem(genre.lower()) for genre in re.split('(core|[\s-])', genre) if genre.strip()]
    ))


def prepare_genre_list(genre):
    regex = '(\s&\s|[/,;])'
    dirty_subs = [sub_genre.strip() for sub_genre in re.split(regex, genre)]
    return list(filter(lambda elem: elem not in regex, dirty_subs))


def build_genre_path_single(root, words):
    current_node = root
    path = [root]
    words = list(reversed(words))

    while True:
        for word in words:
            child = current_node.find(word)
            if child is not None:
                words.remove(word)
                path.append(child)
                current_node = child
                break
        else:
            break
    return path


def build_genre_path_best(root, words):
    fst_try = build_genre_path_single(root, words)
    words.reverse()
    snd_try = build_genre_path_single(root, words)
    return fst_try if len(fst_try) > len(snd_try) else snd_try


if __name__ == '__main__':
    import sys

    try:
        with open('genre_tree.dump', 'rb') as f:
            root = pickle.load(f)
    except OSError:
        root = build_genre_tree()

    root.print()
    for arg in sys.argv[1:]:
        for sub_genre in prepare_genre_list(arg):
            words = prepare_single_genre(sub_genre)
            print('Prepared Words:', words)
            for idx, child in enumerate(build_genre_path_best(root, words)):
                print(' ' * idx, child.genre)

    with open('genre_tree.dump', 'wb') as f:
        pickle.dump(root, f)
