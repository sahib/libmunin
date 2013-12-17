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
    StemProvider

from munin.distance import \
    MoodbarDistance, \
    GenreTreeDistance, \
    BPMDistance


# Checking if the attribute shall be used:
from munin.provider.moodbar import check_for_moodbar
from munin.provider.bpm import check_for_bpmtools


class EasySession(Session):
    @staticmethod
    def from_name():
        return Session.from_name('EasySession')

    def __init__(self):
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
                GenreTreeDistance(),
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
            # TODO: Keyword Provider should be used here.
            'lyrics': pairup(
                WordListProvider() | StemProvider(),
                WordListDistance(),
                3
            )
        }

        if not check_for_moodbar():
            logging.warning('Disabling moodbar attr, no binary found in PATH.')
            del mask['moodbar']

        if not check_for_bpmtools():
            logging.warning("Disabling bpm attr, no binary found in PATH.")
            del mask['bpm']

        Session.__init__(self, 'EasySession', mask)
