#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Get a list of genre via echonest and try to make a Tree out of them:

* Genres:  ::

    Melodic Death Metal
    Pagan Metal
    Japan Pop

* Tree: ::

    music
     +-- pop
     |    +-- japan
     +-- metal
          +-- death
          |    +-- melodic
          +-- pagan


This tree can be then used to map arbitrary genre names to a path in this tree.
The advantage from this is that only paths (== a list of indices)
through the tree can be saved, instead of whole genre strings.
These indices can also be compared very easily.

With above's example: ::

    'Melodic death-metal' = metal -> death -> melodic (Path: 0, 1, 1, 0)
    'Pagan Metal'         = metal -> pagan (Path: 0, 1, 0)
    'Japan Pop Music'     = pop -> japan (Path: 0, 0, 0)

The actual Tree is of course a littler larger and gives you in most cases a path
with 2-3 elements.

Reference
---------
"""

import urllib.request
import pickle
import json
import re

from Stemmer import Stemmer
STEMMER = Stemmer('english')

# Internal imports:
from munin.provider import Provider
from munin.session import get_cache_path, check_or_mkdir


def load_genrelist_from_echonest(dump_path=None):
    """Try yo load a list of genres from echonest (with libglyr's APIKEY)

    This requires a working internet connection obviously.

    :param dump_path: Pickle the list under this path.
    :type dump_path: string
    :returns: a list with ~700 genres.
    """
    URL = 'http://developer.echonest.com/api/v4/artist/list_genres?api_key=ZSIUEIVVZGJVJVWIS&format=json'
    json_file = json.loads(urllib.request.urlopen(URL).read().decode('utf-8'))
    genres = [pair['name'] for pair in json_file['response']['genres']]

    # Pickle the list if desired:
    if dump_path is not None:
        with open(dump_path, 'wb') as f:
            pickle.dump(genres, f)
    return genres


class Tree:
    """
    Modelling a Tree of Genres. Each Tree can be a Node (no children) or
    can contain subgenres.
    """

    def __init__(self, genre, children=None):
        """
        :param genre: The genre.
        'param children: A list of children.'
        """
        self.genre = genre
        self.children = children or []
        self._index = {}

    def build_index_recursively(self):
        """Build a index of self.children (the stemmed genre being the key)"""
        self.children.sort(key=lambda elem: elem.genre)
        for idx, child in enumerate(self.children):
            self._index[STEMMER.stemWord(child.genre)] = idx
            child.build_index_recursively()

    def add(self, child):
        """Add a new child to this node. (child must be Tree)
        If you want to call find() you gonna need to call build_index_recursively()
        """
        self.children.append(child)

    def remove(self, child):
        """Remove a child from the childrens list.
        If you want to call find() you gonna need to call build_index_recursively()
        """
        self.children.remove(child)

    def resolve_path(self, path):
        if not path:
            return ()

        fst, *other = path
        child = self.children[fst]
        return (child.genre, ) + child.resolve_path(other)

    def find_linear(self, genre):
        """Linear scan of the childrens list.

        Works also when build_index_recursively() was not called yet.
        Only used during tree buildup, since this is quite expansive.

        :param genre: The unstemmed genre to search for
        :returns: a tree child
        """
        for child in self.children:
            if child.genre == genre:
                return child

    def find_idx(self, genre):
        """Find a child node's index by it's stemmed genre

        As a prerequesite build_index_recursively must have been called before,
        and no other add or remove operation must have happened.

        :param genre: The stemmed genre.
        :returns: The idx of the desired child in self.children
        """
        # _index is a mapping <stem(genre), index_in_self.children)
        return self._index.get(genre)

    def print_tree(self, _tabs=1, _idx=0):
        """Recursively print the Tree with indentation and the stemmed variation.
        """
        print('    ' * _tabs, '#' + str(_idx), self.genre, STEMMER.stemWord(self.genre).join(('[', ']')))
        for idx, child in enumerate(self.children):
            child.print_tree(_tabs=_tabs + 1, _idx=idx)


def unflatten_list(root):
    """Takes a list of genres stored in root.children and splits them up.

    Example:

        Input: ::

            ['melodic death metal', 'brutal death metal', 'j-pop']

        Output: ::

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
    """
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
    """Recursively calls unflatten_list on root until all nodes are unflattened.
    """
    if unflatten_list(root):
        for child in root.children:
            recursive_unflatten_list(child)


def build_genre_tree():
    """Buildup the genre Tree. On the first run the initial list will be downloaded
    from echonest and cached for later reuse.

    :returns: The root node of the Genre tree.
    """
    # Add a caching layer:
    dump_path = get_cache_path('genre_list.dump')
    try:
        with open(dump_path, 'rb') as f:
            genres = pickle.load(f)
    except (OSError, IOError, AttributeError):
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

    # Make sure find_idx() works - this should be the last operation.
    root.build_index_recursively()
    return root

###########################################################################
#                            Input preparation                            #
###########################################################################


def prepare_single_genre(genre):
    """Prepare a single genre from a genre list by cleaning and stemming it

    :returns: A list of single words in the genre description.
    """
    return list(filter(
        lambda elem: elem != '-',
        [STEMMER.stemWord(g.lower()) for g in re.split('(core|[\s-])', genre) if g.strip()]
    ))


def prepare_genre_list(genre):
    """Split a multi genre description into several single genre descriptions.

    Example: ::

        >>> prepare_genre_list('metalcore; R&B / Folk, Country & Rock')
        ['metalcore', 'R&B', 'Folk', 'Country', 'Rock']

    You should call prepare_single_genre() on every result.

    :returns: A list with single genre descriptions.
    """
    regex = '(\s&\s|[/,;])'
    dirty_subs = [sub_genre.strip() for sub_genre in re.split(regex, genre)]
    return list(filter(lambda elem: elem not in regex, dirty_subs))


###########################################################################
#         Matching Function (delivering a path throught the Tree)         #
###########################################################################

def build_genre_path_single(root, words):
    """Try to map a list of genre words to a path in the tree.

    """
    current_node = root
    path = []
    words = list(reversed(words))

    # Make the iteration iterative, rather than recursive.
    # -m cProfile gave us a little plus of 0.1 seconds.
    while True:
        for word in words:
            pos = current_node.find_idx(word)
            if pos is not None:
                current_node = current_node.children[pos]
                words.remove(word)
                path.append(pos)
                break
        else:
            break

    return [tuple(path)] if path else []


def build_genre_path_best_of_two(root, words):
    """Like build_genre_path_single() but try also the reverse order of the wordlist.

    This sometimes gives better results. It will return the longest path found.
    """
    fst_try = build_genre_path_single(root, words)
    words.reverse()
    snd_try = build_genre_path_single(root, words)
    return sorted(fst_try + snd_try)


def build_genre_path_all(root, words):
    """Get a list of all possible matching genre buildable with the wordlist.

    This is by far more expensive than build_genre_path_single, but will get you
    the best results.
    """
    path_list = []

    def _iterate_recursive(current_root, _mask, _result):
        children = []
        for idx, word in enumerate(words):
            if not _mask[idx]:
                continue

            child_idx = current_root.find_idx(word)
            if child_idx is not None:
                children.append(
                        (idx, child_idx, current_root.children[child_idx])
                )

        if not children and len(_result) > 0:
            path_list.append(_result)

        for word_idx, child_idx, child in children:
            child_mask = list(_mask)
            child_mask[word_idx] = True
            _iterate_recursive(
                    child, _mask=child_mask,
                    _result=_result + (child_idx, )
            )

    _iterate_recursive(root, (True, ) * len(words), ())
    path_list.sort()
    return path_list


def load_genre_tree(pickle_path):
    """Load the genre by either (in this order):

        1) Load it from a locally pickled file as given by pickle_path
        2) Load a list of genres from 'genre_list.dump' and build up the tree.
        3) Load a list of genres from echonest.com and build up the tree.

    :returns: The head of the tree.
    """
    # Load the tree from the disk or rebuild it:
    try:
        with open(pickle_path, 'rb') as fh:
            return pickle.load(fh)
    except (OSError, IOError, AttributeError):
        # AttributeError might happen when the pickle file is invalid.
        check_or_mkdir(get_cache_path(None))
        root = build_genre_tree()

        # Write it to disk for the next time:
        if root is not None:
            with open(pickle_path, 'wb') as f:
                pickle.dump(root, f)
        return root

###########################################################################
#                         Provider Implementation                         #
###########################################################################


class GenreTreeProvider(Provider):
    'Normalize a genre by matching it agains precalculated Tree of sub genres'
    def __init__(self, quality='all', **kwargs):
        """Creates a GenreTreeProvider with a certain quality.

        A GenreTreeProvider will try to normalize a genre by using a Tree of
        705 single genres that will be matched with the input genre in a fast way.

        The result will be a list of Paths. A Path is a tuple of indices, representing
        a possible way through the Tree. For debugging purpose you can use
        GenreTreeProvider.resolve_path() on the path to get the full genre back.

        The Quality levels are:

            - ``all``: Try to find all possible paths through the Tree, sorted
               by the first index (which is useful for comparing.)
            - ``single``: Simply take the first possible path found. Fastest.
            - ``best_two``: Like list, but also uses the reverse word list in a
              second try. Might give better results than 'single' at the cost
              of some speed.

        Default is ``all``.

        This provider is reversible.

        :param quality: One of ``all``, ``best_two``  ``single`` [*default:* ``all``]
        :type quality: String
        """
        Provider.__init__(self, **kwargs)
        self._root = load_genre_tree(get_cache_path('genre_tree.dump'))
        self._build_func = {
            'all': build_genre_path_all,
            'best_two': build_genre_path_best_of_two,
            'single': build_genre_path_single
        }.get(quality, build_genre_path_all)

    def do_process(self, input_value):
        'Subclassed from Provider, will be called for you on the input.'
        result = []
        for sub_genre in prepare_genre_list(input_value):
            words = prepare_single_genre(sub_genre)
            result += self._build_func(self._root, words)
        return tuple(result) or None

    def reverse(self, output_values):
        """Translate the paths in output_values back to genre strings.

        :returns:  A list of genre strings.
        :rtype: [str]
        """
        results = []
        for output_value in output_values:
            val = (' '.join(reversed(self.resolve_path(p))) for p in output_value)
            results.append(tuple(val))
        return tuple(results)

    def resolve_path(self, path):
        """Resolve a path like: ::

            (197, 1, 0)

        to: ::

            ["metal", "death", "brutal"]

        To get back the actual genre, do this: ::

            >>> provider = GenreTreeProvider()
            >>> ' '.join(reversed(provider.resolve_path((197, 1, 0))))
            "brutal death metal"

        or just use :func:`reverse`.

        :param path: The path to resolve.
        :type path: tuple of ints
        :returns: A list of subgenres ordered by specialization.
        :rtype: list of strings
        """
        return self._root.resolve_path(path)


###########################################################################
#                                Test Main                                #
###########################################################################

if __name__ == '__main__':
    import sys

    if not '--cli' in sys.argv:
        import unittest

        class TestGenreTreeProvider(unittest.TestCase):
            def test_process(self):
                test_data = {
                    'metalcore': ['metal core', 'metal'],
                    'Dark Atmospheric Black Funeral Doom Metal': [
                        'funeral doom',
                        'dark black metal',
                        'atmospheric black metal'
                    ]
                }
                prov = GenreTreeProvider()
                for value, expected in test_data.items():
                    resolved = prov.reverse(tuple([prov.process(value)]))
                    for expectation in expected:
                        self.assertTrue(expectation in resolved[0])

        unittest.main()

    ###########################################################################
    #               Other commandline utility for visualization               #
    ###########################################################################
    else:
        if len(sys.argv) < 3:
            print('Usage: {program} --cli "metalcore/melodic death metal"'.format(
                program=sys.argv[0]
            ))
            sys.exit(1)

        root = load_genre_tree(get_cache_path('genre_tree.dump'))

        # Uncomment to get the whole list:
        root.print_tree()

        # Split the genre description and normalize each before finding the path:
        for sub_genre in prepare_genre_list(sys.argv[2]):
            words = prepare_single_genre(sub_genre)

            print()
            print('///////////////')
            print('All Possible  :')
            for path in build_genre_path_all(root, words):
                print('   ', path, root.resolve_path(path))

            paths = build_genre_path_best_of_two(root, words)
            print('Input Genre   :', sub_genre)
            print('Prepared Words:', words)
            print('Result Path   :', paths)
            if paths:
                print('Resolved      :', root.resolve_path(paths[0]))
            print('---------------')

        # Silly graph drawing playground ahead:
        def draw_genre_path(root):
            import networkx as nx
            import matplotlib.pyplot as plt

            # Build up the Tree recursively:
            def recursive(root, _graph=None):
                g = _graph or nx.DiGraph()
                for child in root.children:
                    g.add_edge(root.genre, child.genre)
                    recursive(child, _graph=g)
                return g

            graph = recursive(root)
            nx.draw_networkx(
                graph,
                pos=nx.spring_layout(graph, dim=2, k=0.05, scale=100, iterations=10),
                width=0.2, node_size=150, alpha=0.2, node_color='#A0CBE2',
                font_size=2, arrows=False, node_shape=' '
            )

            plt.savefig("graph.pdf")
            plt.savefig('graph.png', dpi=1000)
        # Uncomment this line to enable graph writing:
        #draw_genre_path(root)
