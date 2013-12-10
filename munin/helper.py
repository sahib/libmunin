#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Contains method that help the user of the library finding the date he needs.

*Helpers*:

    * :class:`AudioFileWalker` - generator class that yields files to audio files.
    * :func:`song_or_uid` - function that delivers the song for uids or just
                            returns the song if passed in.

    * :func:`pairup` - Easy AttributeMask building.

Reference
---------
"""

import os

###########################################################################
#                             AudioFileWalker                             #
###########################################################################


ALLOWED_FORMATS = ['mpc', 'mp4', 'mp3', 'flac', 'wav', 'ogg', 'm4a', 'wma']


class AudioFileWalker:
    '''File Iterator that yields all files with a specific ending.
    '''
    def __init__(self, base_path, extensions=ALLOWED_FORMATS):
        '''There ist a list of default extensions in
        ``munin.helpers.ALLOWED_FORMATS`` with the most common formats.

        This class implements ``__iter__``, so you just can start using it.

        :param base_path: Recursively seach files in this path.
        :param extensions: An iterable of extensions that are allowed.
        '''
        self._base_path = base_path
        self._extension = set(extensions)

    def __iter__(self):
        for root, _, files in os.walk(self._base_path):
            for path in files:
                ending = path.split('.')[-1]
                if ending in self._extension:
                    yield os.path.join(root, path)


###########################################################################
#                               Misc Utils                                #
###########################################################################

def song_or_uid(database, song_or_uid):
    '''Takes a song or the uid of it and return the song.

    This function is purely for your convinience,
    you can always use :func:`munin.database.Database.__getitem__`

    :param database: Database to lookup uid from.
    :raises: IndexError on invalid uid.
    :returns: A :class:`munin.song.Song` in any case.
    '''
    if hasattr(song_or_uid, 'uid'):
        return song_or_uid
    return database[song_or_uid]


def pairup(provider, distance, weight):
    '''Convienience function for easy attribute mask building.

    Every distance function needs to know the provider that processed the value.
    This is needed to implement the compress functionality. In order to stop you
    from writing code like this:

        >>> prov = Provider()
        >>> dfunc = DistanceFunction(prov)
        >>> # Somehwere down:
        >>> {'artist': (prov, dfunc, 0.5)}

    You can just write:

        >>> {'artist': pairup(Provider(), DistanceFunction(), 0.5)}

    This function will set the provider in the DistanceFunction for you.
    '''
    if distance is not None:
        distance._provider = provider
    return (provider, distance, weight)

###########################################################################
#                              Stupid Tests                               #
###########################################################################


if __name__ == '__main__':
    import sys
    walker = AudioFileWalker(sys.argv[1])
    for path in walker:
        print(path)
