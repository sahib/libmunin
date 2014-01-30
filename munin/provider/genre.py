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

# Stdlib:
import pickle
import shelve
import json
import re

from urllib.request import urlopen
from urllib.parse import quote
from collections import Counter

# Internal imports:
from munin.provider import Provider
from munin.session import get_cache_path, check_or_mkdir
from munin.provider.generate_genre_list import load_genrelist


from munin.provider.normalize import \
    ArtistNormalizeProvider, \
    AlbumNormalizeProvider


# External Imports:
from Stemmer import Stemmer
STEMMER = Stemmer('english')


from pyxdameraulevenshtein import \
    normalized_damerau_levenshtein_distance as \
    levenshtein


class Tree:
    """
    Modelling a Tree of Genres. Each Tree can be a Node (no children) or
    can contain subgenres.
    """

    def __init__(self, genre, depth=0, children=None):
        """
        :param genre: The genre.
        'param children: A list of children.'
        """
        self.genre = genre
        self.children = children or []
        self._index = {}
        self.depth = depth

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


def unflatten_list(root, depth):
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
        root.add(Tree(
            genre,
            children=[Tree(g) for g in sub_genres if g],
            depth=depth
        ))
    return was_flattened


def recursive_unflatten_list(root, _depth=1):
    """Recursively calls unflatten_list on root until all nodes are unflattened.
    """
    if unflatten_list(root, _depth):
        for child in root.children:
            recursive_unflatten_list(child, _depth=_depth + 1)


def build_genre_tree():
    """Buildup the genre Tree. On the first run the initial list will be downloaded
    from echonest and cached for later reuse.

    :returns: The root node of the Genre tree.
    """
    # Add a caching layer:
    genres = load_genrelist()

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
            core_node.add(Tree(actual_name, depth=child.depth + 1))
            to_delete.append(child)

    for child in to_delete:
        root.remove(child)

    # 'death core' was somehow there as 'deathcore' too:
    core_node.remove(core_node.find_linear('death'))

    # Add some common not already in:
    for to_add in ['vocal', 'speech']:
        root.add(Tree(to_add, depth=1))

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
    return sorted(set(fst_try + snd_try))


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
#                         Discogs Genre Provider                          #
###########################################################################


DISCOGS_API_SEARCH_URL = "http://api.discogs.com/database/search?type=release&q={artist}"


def _filter_crosslinks(genre_set, style_set):
    for key in genre_set:
        if key in style_set:
            del style_set[key]


def _filter_spam(counter):
    if not counter:
        return

    avg = sum(counter.values()) // len(counter)
    for key in list(counter):
        if counter[key] < avg:
            del counter[key]


def _find_right_genre(json_doc, artist, album, persist_on_album):
    """
    Try to read the correct genre from the json document by discogs.

    :param artist: a normalized artist
    :param album: a normalized album.
    :param persist_on_album: If False, other albums of this artist are valid sources too.
    :returns: A set of music genres (i.e. rock) and a set of styles (i.e. death metal)
    """
    genre_set, style_set = Counter(), Counter()
    for item in json_doc['results']:
        # Some artist items have not a style in them.
        # Skip these items.
        if 'style' not in item:
            continue

        # Get the remote artist/album from the title, also normalise them.
        artist_normalizer = ArtistNormalizeProvider()
        album_normalizer = AlbumNormalizeProvider()
        remote_artist, remote_album = item['title'].split(' - ', maxsplit=1)
        remote_artist, *_ = artist_normalizer.do_process(remote_artist)
        remote_album, *_ = album_normalizer.do_process(remote_album)

        # Try to outweight spelling errors, or small
        # pre/suffixes to the artist. (i.e. 'the beatles' <-> beatles')
        if levenshtein(artist, remote_artist) > 0.5:
            continue

        # Same for the album:
        if persist_on_album and levenshtein(album, remote_album) > 0.5:
            continue

        # Remember the set of all genres and styles.
        genre_set.update(item['genre'])
        style_set.update(item['style'])

    _filter_spam(genre_set)
    _filter_spam(style_set)
    _filter_crosslinks(genre_set, style_set)
    return genre_set, style_set


def find_genre_via_discogs(artist, album):
    """
    Try to find the genre from discogs.com using only the artist and album
    as base.

    The following strategy is taken:

        1) Try to find the artist/album combinations using
           levenshtein fuzzy matching.
        2) If the exact combinations was not found the genre
           is taken from the other known albums of this artist.

    The resulting genre may not very informative for humans, but is easily
    split into seperate sub-genres by the GenreTreeProvider, which is good
    for comparasions.

    Future versions might include a version that tries to find a more
    human readable string.

    Example output: ::

        Genre: Non-Music; Folk, World, & Country; Stage & Screen / Comedy, Monolog, Spoken Word, Political

    .. note::

        Tip: Use :class:`munin.distance.GenreTreeAvgLinkDistance` with this data.
        The normal :class:`munin.distance.GenreTreeProvider` uses Single Linkage,
        which may give too good distances often enough.

    :param artist: The artist string to search for (gets normalised)
    :param album: The album string to search for (gets normalised)
    :returns: A genre string like in the example or None.
    """
    # Get the data from discogs
    api_root = DISCOGS_API_SEARCH_URL.format(artist=quote(artist))
    html_doc = urlopen(api_root).read().decode('utf-8')
    json_doc = json.loads(html_doc)

    # Normalize the input artist/album
    artist_normalizer = ArtistNormalizeProvider()
    album_normalizer = AlbumNormalizeProvider()
    artist, *_ = artist_normalizer.do_process(artist)
    album, *_ = album_normalizer.do_process(album)

    genre_set, style_set = _find_right_genre(json_doc, artist, album, True)
    if not (genre_set or style_set):
        # Lower the expectations, just take the genre of
        # all known albums of this artist, if any:
        genre_set, style_set = _find_right_genre(json_doc, artist, album, False)

    # Still not? Welp.
    if not (genre_set or style_set):
        return None

    # Bulid a genre string that is formatted this way:
    #  genre1; genre2 [;...] / style1, style2, style3 [,...]
    #  blues, rock / blues rock, country rock, christian blues
    return ' / '.join((
        ', '.join(k for k, v in genre_set.most_common(3)),
        ', '.join(k for k, v in style_set.most_common(4))
    ))


class DiscogsGenreProvider(Provider):
    """
    Use :func:`find_genre_via_discogs` to find the genre of a song automatically.

    This is provided for convinience if you want to fetch the genre
    automatically. Additionaly caching of the results is available.
    """
    def __init__(self, use_cache=True, cache_fails=True, **kwargs):
        """
        :param use_cache: Cache found results?
        :param cache_fails: Also cache missed results?
        """
        Provider.__init__(self, **kwargs)
        self._use_cache, self._cache_fails = use_cache, cache_fails
        self._shelve = shelve.open(
            get_cache_path('discogs_genre.dump'),
            writeback=True
        )

    def do_process(self, artist_album):
        key = '__'.join(artist_album)
        if self._use_cache and key in self._shelve:
            return self._shelve[key]

        genre = find_genre_via_discogs(*artist_album)
        if self._cache_fails or genre is not None:
            self._shelve[key] = genre
            self._shelve.sync()
        return genre


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
                print('Resolved      :', [root.resolve_path(path) for path in paths])
            print('---------------')

        # Silly graph drawing playground ahead:
        def draw_genre_path(root, min_saturation=0.0):
            from itertools import cycle
            from collections import deque

            nodes = deque([root])
            lines = deque()

            colors = [
                '0.000 {:1.3f} 0.850',
                '0.050 {:1.3f} 0.850',
                '0.100 {:1.3f} 0.850',
                '0.150 {:1.3f} 0.850',
                '0.200 {:1.3f} 0.850',
                '0.250 {:1.3f} 0.850',
                '0.300 {:1.3f} 0.850',
                '0.350 {:1.3f} 0.850',
                '0.450 {:1.3f} 0.850'
            ]

            while nodes:
                node = nodes.popleft()
                if not node.children:
                    continue

                for child in node.children:
                    saturation = min(8, len(child.children)) / 8
                    if saturation >= min_saturation:
                        lines.append(
                            'node [shape="none", style="rounded, filled", fillcolor="{color}", fontcolor="black" fontsize="{size}"]'.format(
                                color=colors[child.depth].format(min(0.75, saturation)),
                                size=max(8, saturation * 25)
                            )
                        )
                        lines.append(
                            '"  {l}  " -- "  {r}  "'.format(l=node.genre, r=child.genre)
                        )
                        nodes.append(child)

            with open('/tmp/genre.graph', 'w') as handle:
                handle.write('''
                /*
                * python munin/provider/genre.py --cli --plot 0.0
                * sfdp /tmp/genre.graph | gvmap -e | neato -n2 -Ecolor="#55555555" -Nfontname="TeX Gyre Adventor" -Tpng > graph.png && sxiv graph.png
                */
                graph GenreGraph
                {
                    overlap=prism3000
                    overlap_scale=-7
                    splines=curved

                    edge [color="#666666"]
                    node [shape="rectangle", style="rounded", fillcolor="white", fontcolor="black" fontsize=50]

                    "  music  "

                ''' + '\n'.join(lines) + '}')

        if '--plot' in sys.argv:
            draw_genre_path(root, float(sys.argv[3]))
