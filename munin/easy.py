#!/usr/bin/env python
# encoding: utf-8

"""
A "easy" version of the Session object where you do not have to set the attribute mask yourself.

Instead a number of preconfigured number of attributes are selected that
are know to work well together.
"""

from munin.session import Session
from munin.helper import pairup

from munin.provider import LancasterStemProvider
from munin.provider import MoodbarAudioFileProvider
from munin.provider import GenreTreeProvider

# from munin.distance.steam import S
from munin.distance import MoodbarDistance
from munin.distance import GenreTreeDistance


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
    def __init__(self, name='EasySession'):
        Session.__init__(self, name, {
            'artist': pairup(
                LancasterStemProvider(compress=True),
                None,
                0.1
            ),
            'album': pairup(
                LancasterStemProvider(compress=True),
                None,
                0.1
            ),
            'title': pairup(
                LancasterStemProvider(compress=False),
                None,
                0.1
            ),
            'genre': pairup(
                GenreTreeProvider(),
                GenreTreeDistance(),
                0.2
            ),
            'moodbar': pairup(
                MoodbarAudioFileProvider(),
                MoodbarDistance(),
                0.5
            ),
            'lyrics': pairup(
                WordListProvider(),
                WordListDistance(),
                0.3
            )
        })
