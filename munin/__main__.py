#!/usr/bin/env python
# encoding: utf-8

from munin.session import Session
from munin.provider import AtticProvider, GenreTreeProvider
from munin.distance import GenreTreeDistance


def main():
    # Perhaps we already had an prior session?
    session = Session.from_name(__name__)
    if session is None:
        # Looks like it didn't exist yet.
        # Well, go and create it!
        session = Session(
            name='MyNameIsSession',
            attribute_mask={
                # Each line goes like this:
                # 'the-key-you-want-have-in-your-song': (Provider, DistanceFunction, Weighting)
                'genre': (GenreTreeProvider, GenreTreeDistance, 0.5),
                'title': (StemProvider, WordlistDistance, 0.1),
                'artist': (AtticProvider, None, 0.1)
            }
        )

        # TODO: Make this somewhat clearer.
        with session.transaction():
            for song in your_database:
                session.add(song)

    # In any case: We have a running session now.
    # We can now use to do useful stuff like recomnendations:
    pass


if __name__ == '__main__':
    pass
