#!/usr/bin/env python
# encoding: utf-8

"""
A "easy" version of the Session object where you do not have to set the mask yourself.

Instead a number of preconfigured number of attributes are selected that
are know to work well together.
"""

import logging
LOGGER = logging.getLogger(__name__)


from munin.session import Session
from munin.helper import pairup

from munin.provider import \
    ArtistNormalizeProvider, \
    AlbumNormalizeProvider, \
    TitleNormalizeProvider, \
    MoodbarAudioFileProvider, \
    GenreTreeProvider, \
    BPMCachedProvider, \
    StemProvider, \
    KeywordsProvider

from munin.distance import \
    MoodbarDistance, \
    GenreTreeAvgLinkDistance, \
    BPMDistance, \
    KeywordsDistance, \
    RatingDistance


# Checking if the attribute shall be used:
from munin.provider.moodbar import check_for_moodbar
from munin.provider.bpm import check_for_bpmtools
from munin.provider.keywords import check_for_plyr


class EasySession(Session):
    @staticmethod
    def from_name(name='EasySession'):
        return Session.from_name(name)

    def __init__(self, name='EasySession', disabled_attrs=None):

        mask = {
            'artist': pairup(
                ArtistNormalizeProvider(compress=True),
                None,
                1
            ),
            'album': pairup(
                AlbumNormalizeProvider(compress=True),
                None,
                1
            ),
            'title': pairup(
                TitleNormalizeProvider(compress=False) | StemProvider(),
                None,
                1
            ),
            'genre': pairup(
                GenreTreeProvider(),
                GenreTreeAvgLinkDistance(),
                2
            ),
            'bpm': pairup(
                BPMCachedProvider(),
                BPMDistance(),
                3
            ),
            'moodbar': pairup(
                MoodbarAudioFileProvider(),
                MoodbarDistance(),
                5
            ),
            'lyrics': pairup(
                KeywordsProvider(),
                KeywordsDistance(),
                3
            ),
            'rating': pairup(
                None,
                RatingDistance(),
                3
            )
        }

        if not check_for_moodbar():
            logging.warning('Disabling moodbar attr, no binary found in PATH.')
            del mask['moodbar']

        if not check_for_bpmtools():
            logging.warning("Disabling bpm attr, no binary found in PATH.")
            del mask['bpm']

        for disabled_attr in disabled_attrs or []:
            try:
                del mask[disabled_attr]
            except KeyError:
                pass

        Session.__init__(self, name, mask)
