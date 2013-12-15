#!/usr/bin/env python
# encoding: utf-8

"""
A "easy" version of the Session object where you do not have to set the attribute mask yourself.

Instead a number of preconfigured number of attributes are selected that
are know to work well together.
"""

import logging
LOGGER = logging.getLogger(__name__)


from munin.session import Session
from munin.helper import pairup

from munin.provider import LancasterStemProvider
from munin.provider import MoodbarAudioFileProvider
from munin.provider import GenreTreeProvider

from munin.distance import MoodbarDistance
from munin.distance import GenreTreeDistance

# Checking if the attribute shall be used:
from munin.provider.moodbar import check_for_moodbar
from munin.provider.bpm import check_for_bpmtools


# Providers to write:
#    WordlistProvider
#    BPMProvider
#    NotInProvider
#
# Distance to write:
#    NotInDistance
#    StemDistance
#    BPMDistance
#    WordListDistance

class EasySession(Session):
    @staticmethod
    def from_name():
        return Session.from_name('EasySession')

    def __init__(self):
        mask = {
            'artist': pairup(
                LancasterStemProvider(compress=True),
                None,
                1
            ),
            'album': pairup(
                LancasterStemProvider(compress=True),
                None,
                1
            ),
            'title': pairup(
                LancasterStemProvider(compress=False),
                None,
                1
            ),
            'genre': pairup(
                GenreTreeProvider(),
                GenreTreeDistance(),
                2
            ),
            'moodbar': pairup(
                MoodbarAudioFileProvider(),
                MoodbarDistance(),
                5
            ),
            'lyrics': pairup(
                WordListProvider(),
                WordListDistance(),
                3
            )
        }

        if not check_for_moodbar():
            logging.warning('Disabling moodbar attribute, no binary found in PATH.')
            del mask['moodbar']

        if not check_for_bpmtools():
            logging.warning("Disabling bpm attribute, no binary found in PATH.")
            del mask['bpm']

        Session.__init__('EasySession', mask)
