#!/usr/bin/env python
# encoding: utf-8

import urllib.request
import pickle
import json
import re

# Pure Python Stemmer - slow as fuck.
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


This tree can be then used to map arbitrary genre names to a path in this tree.
The advantage from this is that only paths (== a list of indices)
through the tree can be saved, instead of whole genre strings.
These indices can also be compared very easily.

With above's example:

    'Melodic death-metal' = metal -> death -> melodic (Path: 0, 1, 1, 0)
    'Pagan Metal'         = metal -> pagan (Path: 0, 1, 0)
    'Japan Pop Music'     = pop -> japan (Path: 0, 0, 0)
'''


def load_genrelist_from_echonest(dump_path=None):
    '''Try yo load a list of genres from echonest (with libglyr's APIKEY)

    This requires a working internet connection obviously.

    :param dump_path: Pickle the list under this path.
    :returns: a list with ~700 genres.
    '''
    URL = 'http://developer.echonest.com/api/v4/artist/list_genres?api_key=ZSIUEIVVZGJVJVWIS&format=json'
    json_file = json.loads(urllib.request.urlopen(URL).read().decode('utf-8'))
    genres = [pair['name'] for pair in json_file['response']['genres']]

    # Pickle the list if desired:
    if dump_path is not None:
        with open(dump_path, 'wb') as f:
            pickle.dump(genres, f)
    return genres


class Tree:
    '''
    Modelling a Tree of Genres. Each Tree can be a Node (no children) or
    can contain subgenres.
    '''

    def __init__(self, genre, children=None):
        '''
        :param genre: The genre.
        'param children: A list of children.'
        '''
        self.genre = genre
        self.children = children or []
        self._index = {}

    def build_index_recursively(self):
        '''Build a index of self.children (the stemmed genre being the key)'''
        for idx, child in enumerate(self.children):
            self._index[stem(child.genre)] = idx
            child.build_index_recursively()

    def add(self, child):
        '''Add a new child to this node. (child must be Tree)
        If you want to call find() you gonna need to call build_index_recursively()
        '''
        self.children.append(child)

    def remove(self, child):
        '''Remove a child from the childrens list.
        If you want to call find() you gonna need to call build_index_recursively()
        '''
        self.children.remove(child)

    def find_linear(self, genre):
        '''Linear scan of the childrens list.

        Works also when build_index_recursively() was not called yet.
        Only used during tree buildup, since this is quite expansive.

        :param genre: The unstemmed genre to search for
        :returns: a tree child
        '''
        for child in self.children:
            if child.genre == genre:
                return child

    def find(self, genre):
        '''Find a child node by it's stemmed genre

        As a prerequesite build_index_recursively must have been called before,
        and no other add or remove operation must have happened.

        :param genre: The stemmed genre.
        '''
        # _index is a mapping <stem(genre), index_in_self.children)
        pos = self._index.get(genre)
        if pos is not None:
            return self.children[pos]

    def print_tree(self, _tabs=1):
        '''Recursively print the Tree with indentation and the stemmed variation.
        '''
        print('    ' * _tabs, self.genre, stem(self.genre).join(('[', ']')))
        for child in self.children:
            child.print_tree(_tabs=_tabs + 1)


def unflatten_list(root):
    '''Takes a list of genres stored in root.children and splits them up.

    Example:

        Input: ['melodic death metal', 'brutal death metal', 'j-pop']
        Output:

            metal
            |-melodic death
            |-brutal deah
            pop
            |-j

    The child objects will be Trees, with the rest of the split filled.
    These subgenres should be used with this functions again.
    If nothing is there to split this function will return False and will not
    change the input.

    :param child: Any Node that has subgenres that need to be split.
    :returns: True if at least one successful split was done.
    '''
    genre_mapping = {}
    was_flattened = False

    for child in root.children:
        *rest, last = re.split('[-\s]', child.genre)
        if rest:
            was_flattened = True

        sub_genres = genre_mapping.setdefault(last, set())
        if not sub_genres or rest:
            sub_genres.add(' '.join(rest))

    root.children = []
    for genre, sub_genres in genre_mapping.items():
        root.add(Tree(genre, children=[Tree(g) for g in sub_genres if g]))
    return was_flattened


def recursive_unflatten_list(root):
    '''Recursively calls unflatten_list on root until all nodes are unflattened.
    '''
    if unflatten_list(root):
        for child in root.children:
            recursive_unflatten_list(child)


def build_genre_tree():
    '''Buildup the genre Tree. On the first run the initial list will be downloaded
    from echonest and cached for later reuse.

    :returns: The root node of the Genre tree.
    '''
    # Add a caching layer:
    dump_path = '/tmp/genre_list.dump'
    try:
        with open(dump_path, 'rb') as f:
            genres = pickle.load(f)
    except OSError:
        genres = load_genrelist_from_echonest(dump_path)

    # Create the root node ('music' is always optional)
    root = Tree('music', children=[Tree(genre) for genre in genres])

    # Unflatten all node, actually build the tree.
    recursive_unflatten_list(root)

    # Manual corrections:
    # Fix the 'music' Node
    # Just pull all subgenres on layer up.
    music_node = root.find_linear('music')
    for child in music_node.children:
        root.add(child)
    root.remove(music_node)

    # Fix the core genres manually to be a subgenre of 'core'
    to_delete = []
    core_node = root.find_linear('core')
    for child in root.children:
        if 'core' in child.genre and child.genre != 'core':
            actual_name, *_ = child.genre.split('core')
            core_node.add(Tree(actual_name))
            to_delete.append(child)

    for child in to_delete:
        root.remove(child)

    # 'death core' was somehow there as 'deathcore' too:
    core_node.remove(core_node.find_linear('death'))

    # Add some common not already in:
    for to_add in ['vocal', 'speech']:
        root.add(Tree(to_add))

    # Make sure find() works - this should be the last operation.
    root.build_index_recursively()
    return root


def prepare_single_genre(genre):
    '''Prepare a single genre from a genre list by cleaning and stemming it

    :returns: A list of single words in the genre description.
    '''
    # TODO: Decide if we should split by 'core' or not. (can't harm?)
    return list(filter(
        lambda elem: elem != '-',
        [stem(genre.lower()) for genre in re.split('(core|[\s-])', genre) if genre.strip()]
    ))


def prepare_genre_list(genre):
    '''Split a multi genre description into several single genre descriptions.

    Example: ::

        >>> prepare_genre_list('metalcore; R&B / Folk, Country & Rock')
        ['metalcore', 'R&B', 'Folk', 'Country', 'Rock']

    You should call prepare_single_genre() on every result.

    :returns: A list with single genre descriptions.
    '''
    regex = '(\s&\s|[/,;])'
    dirty_subs = [sub_genre.strip() for sub_genre in re.split(regex, genre)]
    return list(filter(lambda elem: elem not in regex, dirty_subs))


def build_genre_path_single(root, words):
    '''Try to map a list of genre words to a path in the tree.

    # TODO: Make this integers.
    '''
    current_node = root
    path = [root]
    words = list(reversed(words))

    # Make the iteration iterative, rather than recursive.
    # -m cProfile gave us a little plus of 0.1 seconds.
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
    '''Like build_genre_path_single() but try also the reverse order of the wordlist.

    This sometimes gives better results. It will return the longest path found.
    '''
    fst_try = build_genre_path_single(root, words)
    words.reverse()
    snd_try = build_genre_path_single(root, words)
    return fst_try if len(fst_try) > len(snd_try) else snd_try


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: {program} "metalcore/melodic death metal"'.format(
            program=sys.argv[0]
        ))
        sys.exit(1)

    # Load the tree from the disk or rebuild it:
    try:
        with open('genre_tree.dump', 'rb') as f:
            root = pickle.load(f)
    except OSError:
        root = build_genre_tree()

    # Split the genre description and normalize each before finding the path:
    for sub_genre in prepare_genre_list(sys.argv[1]):
        words = prepare_single_genre(sub_genre)
        print('Prepared Words:', words)
        for idx, child in enumerate(build_genre_path_best(root, words)):
            print(' ' * idx, child.genre)

    with open('genre_tree.dump', 'wb') as f:
        pickle.dump(root, f)

    # Silly graph drawing playground ahead:
    def draw_genre_path(root):
        import networkx as nx
        import matplotlib.pyplot as plt

        # Build up the Tree recursively:
        def recursive(root, _graph=None):
            g = _graph or nx.DiGraph()

            for child in root.children:
                if root.genre == 'edge' or child.genre == 'edge':
                    continue
                g.add_edge(root.genre, child.genre)
                recursive(child, _graph=g)
            return g

        graph = recursive(root)
        nx.draw_networkx(
             graph, pos=nx.spring_layout(graph, dim=2, k=0.05, scale=100, iterations=10),
             width=0.2, node_size=150, alpha=0.2, node_color='#A0CBE2', font_size=2, arrows=False, node_shape=' '
        )

        plt.savefig("graph.pdf")
        plt.savefig('graph.png', dpi=1000)

    # Uncomment this line to enable graph writing:
    #draw_genre_path(root)
