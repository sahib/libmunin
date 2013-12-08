#!/usr/bin/env python
# encoding: utf-8

from munin.session import Session
from munin.provider import GenreTreeProvider
from munin.distance import GenreTreeDistance


# Part 1: Creating a session
# Part 2: Loading a session
# Part 3: Mapping your songs to munin's internal songs.
# Part 4: Getting recommendations
# Part 5: Feeding the History
# Part 6: Adding/Removing single songs
# Part 7: Accessing rules
# Part 8: Data-Retrieval Helpers (scripts)
# Part 9: EasySession and AyncSession


'''
API TODOS:

- Methods should take uid or songs
- session.database.rule_index
- AudioFileWalker -- done
- Delete Songs -> delete according rules? Nope, nur beim rebuild.
- recommend_from_seed()
- recommend()


Session:

    add / add
    insert_song / remove_song
    feed_history
    attribute_mask
    config
    recommend_global()
    recommend_from_seed()


'''

# Well, let's just use fake data. You should load here your actual database!
MY_DATABASE = [
    ('metal', 'Devildriver', 'Before the Hangmans Noose'),
    ('folk', 'Das Niveau', 'Beim Pissen gemeuchelt'),
    ('metal', 'We Butter the Bread with Butter', 'Extrem')
]


# Part 1:
# This will be always called "on the first run".
def create_new_session():
    session = Session(
        name=__name__,
        attribute_mask={
            # Each line goes like this:
            # 'the-key-you-want-have-in-your-song': (Provider, DistanceFunction, Weighting)
            'genre': (GenreTreeProvider, GenreTreeDistance, 0.5),
            'title': (StemProvider, WordlistDistance, 0.1),
            'artist': (None, None, 0.1)
        }
    )

    # Now we have an empty session. We somehow need to get the songs into it...
    with session.transaction():
        for idx, (genre, artist, title) in enumerate(MY_DATABASE):
            # session.add returns the newly created munin song
            # Each session has a mapping field, which is simply a dictionary.
            # This dictionary can be used to remember the relation between
            # munin's songs and the song in our own database.
            # Plus: it gets saved when dumping the session to a file.
            # Note: The usage of mapping is in your own responsibility.
            session.mapping[session.add({
                'genre': genre,
                'title': title,
                'artist': artist,
            })] = idx

    return session


# Part 4:
def print_recommendations(session):
    # A generator that yields at max 20 songs.
    recom_generator = session.recommendations(n=20)
    for munin_song in recom_generator:
        print('Normalized Values')
        for attribute, normalized_value in munin_song.items():
            print('    {:>20s}: {}'.format(attribute, normalized_value))

        original_song = MY_DATABASE[session.mapping[munin_song]]
        print('Original Song:', original_song)


if __name__ == '__main__':
    # Part 2:
    # Perhaps we already had an prior session?
    session = Session.from_name(__name__) or create_new_session()

    print_recommendations(session)

    # Part 5:
    # Let's say we listened the first song twice, the last song once:
    # TODO: Support uid and song
    session.database.feed_history(session.database.lookup(0))
    session.database.feed_history(session.database.lookup(0))
    session.database.feed_history(session.database.lookup(2))

    with session.fixing():
        new_uid = session.database.insert_song({
            'genre': 'pop',
            'title': 'Pokerface',
            'artist': 'Lady Gaga',
        })

    # Part 7:
    for rule in session.database.rule_index:
        print(rule)

    for rule in session.database.rule_index.lookup(0):
        print(rule)

    # Part 8:
    from munin.scripts import AudioFileWalker
    for audio_path in AudioFileWalker('~/hd/music'):
        pass
