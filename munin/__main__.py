#!/usr/bin/env python
# encoding: utf-8

from munin.helper import pairup
from munin.session import Session
from munin.distance import GenreTreeDistance, WordlistDistance
from munin.provider import \
        GenreTreeProvider, \
        WordlistProvider,  \
        Provider,          \
        StemProvider


MY_DATABASE = [(
        'Devildriver',                # Artist
        'Before the Hangmans Noose',  # Title
        'metal'                       # Genre
    ), (
        'Das Niveau',
        'Beim Pissen gemeuchelt',
        'folk'
    ), (
        'We Butter the Bread with Butter',
        'Extrem',
        'metal'
)]


def create_session(name):
    session = Session(
        name='demo',
        attribute_mask={
            # Each entry goes like this:
            'Genre': pairup(
                # Pratice: Go lookup what this Providers does.
                GenreTreeProvider(),
                # Practice: Same for the DistanceFunction.
                GenreTreeDistance(),
                # This has the highest rating of the three attributes:
                8
            ),
            'Title': pairup(
                # We can also compose Provider, so that the left one
                # gets the input value, and the right one the value
                # the left one processed.
                # In this case we first split the title in words,
                # then we stem each word.
                WordlistProvider() | StemProvider(),
                WordlistDistance(),
                1
            ),
            'Artist': pairup(
                # If no Provider (None) is given the value is forwarded as-is.
                # Here we just use the default provider, but enable
                # compression. Values are saved once and are givean an ID.
                # Duplicate items get the same ID always.
                # You can trade off memory vs. speed with this.
                Provider(compress=True),
                # If not DistanceFunctions is given, all values are
                # compare with __eq__ - which might give bad results.
                None,
                1
            )
        }
    )

    # As in our first example we fill the session:
    with session.transaction():
        for idx, (artist, title, genre) in enumerate(MY_DATABASE):
            # Notice how we use the uppercase keys like above:
            session.mapping[session.add({
                'Genre': genre,
                'Title': title,
                'Artist': artist,
            })] = idx

    return session


def print_recommendations(session, n=5):
    # A generator that yields at max 20 songs.
    recom_generator = session.recommendations_from_graph(n=n)
    for munin_song in recom_generator:
        print('Normalized Values')

        # Let's take
        for attribute, normalized_value in munin_song.items():
            print('    {:>20s}: {}'.format(attribute, normalized_value))

        original_song = MY_DATABASE[session.mapping[munin_song]]
        print('Original Song:', original_song)


if __name__ == '__main__':
    # Perhaps we already had an prior session?
    session = Session.from_name('demo') or create_session('demo')

    # Let's add some history:
    for munin_uid in [0, 2, 0, 0, 2]:
        session.feed_history(munin_uid)

    print(session.playcounts())  # {0: 3, 1: 0, 2: 2}

    print_recommendations(session)  # Prints last and second song.

    # Let's insert a new song that will be in the graph on the next run:
    with session.fixing():
        session.mappin[session.insert({
            'genre': 'pop',
            'title': 'Pokerface',
            'artist': 'Lady Gaga',
        })] = len(MY_DATABASE)

    # Save it under ~/.cache/libmunin/demo
    session.save()
