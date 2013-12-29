#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------


Reference
---------
"""

import logging
LOGGER = logging.getLogger(__name__)


from munin.provider import Provider
from munin.session import get_cache_path
from munin.rake import extract_keywords

try:
    import plyr
    HAS_PLYR = True
except ImportError:
    HAS_PLYR = False
    LOGGER.debug('No plyr support enabled')


class KeywordsProvider(Provider):
    """Splits an arbitary text into a list of keywordsets.

    Each keywordset contains one more words that are considered to be repeated
    often or that are distinct in the text.

    **Takes:** An arbitary text, or a one-element tuple with a string.
    **Gives:** A list of keywordsets, similar to the WordlistProvider.
    """
    def do_process(self, text):
        if isinstance(text, tuple):
            text = text[0]

        keywords_map = extract_keywords(text)
        return [keys for keys, rating in keywords_map.items() if rating > 1.0][:10]


def check_for_plyr():
    """Returns True if the plyr lyrics provider is available"""
    return HAS_PLYR


class PlyrLyricsProvider(Provider):
    """Retrieve a lyrics text from the web using libglyr.

    .. note::

        Many people have `.lyrics` files along their music files. This is *not*
        checked here, although libglyr is capable of that.

    **Takes:** A tuple of (artist, title), **outputs** a one-element tuple with
    the lyrics text in it.

    **Example Usage:**

        .. code-block:: python


            >>> p = PlyrLyricsProvider()
            >>> p.do_process(('Akrea', 'Trugbild'))
            ('lots of text', )

    In the :term:`Mask` it should be used as:

        .. code-block:: python

            PlyrLyricsProvider() | KeywordsProvider()

    .. warning::

        If a artist/title combination is not found the result is remembered.
        If you do not want this behaviour set the ``cache_failures`` argument
        to False. ::

            >>> PlyrLyricsProvider(cache_failures=False)

    .. note::

        When feeding tags from your music database as artist/title
        it is recommended to use the album_artist and the track_artist
        as fallback.

    """
    def __init__(self, **kwargs):
        if not HAS_PLYR:
            raise LookupError('Plyr could be imported, which is needed for lyrics')

        self._cache_failures = kwargs.pop('cache_failures', True)
        self.database = plyr.Database(get_cache_path(None))

        Provider.__init__(self, **kwargs)

    def do_process(self, artist_title):
        artist, title = artist_title
        LOGGER.debug('artist={a} title={t} ({v})'.format(
            a=artist, t=title, v=plyr.version()
        ))

        qry = plyr.Query(
            get_type='lyrics',
            artist=artist,
            title=title,
            database=self.database,
            parallel=4,
            timeout=5
        )
        items = qry.commit()

        if items:
            first = items[0]

            # This item was cached on failure:
            if first.rating is -1:
                return None

            try:
                return (first.data.decode('utf-8'), )
            except UnicodeDecodeError:
                pass

        if self._cache_failures:
            dummy = self.database.make_dummy()
            self.database.insert(qry, dummy)
        return None


if __name__ == '__main__':
    import sys

    if '--cli' in sys.argv:
        prov = PlyrLyricsProvider() | KeywordsProvider()
        for kwset in prov.do_process((sys.argv[2], sys.argv[3])):
            print(list(kwset))
