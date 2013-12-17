#!/usr/bin/env python
# encoding: utf-8

import sys

from munin.helper import pairup
from munin.session import Session
from munin.distance import GenreTreeDistance, WordlistDistance
from munin.provider import \
        ArtistNormalizeProvider, \
        GenreTreeProvider, \
        WordlistProvider,  \
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
    ), (
        'Lady Gaga',
        'Pokerface',
        'pop'
)]


def create_session(name):
    print('-- No saved session found, loading new.')
    session = Session(
        name='demo',
        mask={
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
                ArtistNormalizeProvider(compress=True),
                # If not DistanceFunctions is given, all values are
                # compare with __eq__ - which might give bad results.
                None,
                1
            )
        }
    )

    # As in our first example we fill the session, but we dont insert the full
    # database, we leave out the last song:
    with session.transaction():
        for idx, (artist, title, genre) in enumerate(MY_DATABASE[:3]):
            # Notice how we use the uppercase keys like above:
            session.mapping[session.add({
                'Genre': genre,
                'Title': title,
                'Artist': artist,
            })] = idx

    return session


def print_recommendations(session, n=5):
    # A generator that yields at max 20 songs.
    recom_generator = session.recommend_from_heuristic(number=n)
    seed_song = next(recom_generator)
    print('Recommendations to #{}:'.format(seed_song.uid))
    for munin_song in recom_generator:
        print('  normalized values:')

        # Let's take
        for attribute, normalized_value in munin_song.items():
            print('    {:<7s}: {:<20s}'.format(attribute, normalized_value))

        original_song = MY_DATABASE[session.mapping[munin_song.uid]]
        print('  original values:')
        print('    Artist :', original_song[0])
        print('    Album  :', original_song[1])
        print('    Genre  :', original_song[2])
        print()


if __name__ == '__main__':
    print('The database:')
    for idx, song in enumerate(MY_DATABASE):
        print('  #{} {}'.format(idx, song))
    print()

    # Perhaps we already had an prior session?
    session = Session.from_name('demo') or create_session('demo')
    rules = list(session.rule_index)
    if rules:
        print('Association Rules:')
        for left, right, support, rating in rules:
            print('  {:>10s} <-> {:<10s} [supp={:>5d}, rating={:.5f}]'.format(
                str([song.uid for song in left]),
                str([song.uid for song in right]),
                support, rating
            ))
        print()

    print_recommendations(session)

    # Let's add some history:
    for munin_uid in [0, 2, 0, 0, 2]:
        session.feed_history(munin_uid)

    print('Playcounts:')
    for song, count in session.playcounts().items():
        print('  #{} was played {}x times'.format(song.uid, count))

    # Let's insert a new song that will be in the graph on the next run:
    if len(session) != len(MY_DATABASE):
        with session.fix_graph():
            session.mapping[session.insert({
                'Genre': MY_DATABASE[-1][2],
                'Title': MY_DATABASE[-1][1],
                'Artist': MY_DATABASE[-1][0]
            })] = 3

    if '--plot' in sys.argv:
        session.database.plot()

    # Save it under ~/.cache/libmunin/demo
    session.save()
