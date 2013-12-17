import sys

from munin.easy import EasySession


MY_DATABASE = [
    # Artist:            Album:               Title:             Genre:
    ('Akrea'          , 'Lebenslinie'      , 'Trugbild'       , 'death metal'),
    ('Vogelfrey'      , 'Wiegenfest'       , 'Heldentod'      , 'folk metal'),
    ('Letzte Instanz' , 'Götter auf Abruf' , 'Salve te'       , 'folk rock'),
    ('Debauchery'     , 'Continue to Kill' , 'Apostle of War' , 'brutal death')
]


session = EasySession()
with session.transaction():
    for idx, (artist, album, title, genre) in enumerate(MY_DATABASE):
         session.mapping[session.add({
             'artist': artist,
             'album': album,
             'title': title,
             'genre': genre
         })] = idx


print('2 Recommendations to: {}'.format(MY_DATABASE[0]))
for munin_song in session.recommend_from_seed(session[0], 2):
    print('    ', MY_DATABASE[munin_song.uid])


print('3 Recommendations to: {}'.format(MY_DATABASE[1]))
for munin_song in session.recommend_from_seed(session[1], 3):
    print('    ', MY_DATABASE[munin_song.uid])


if '--plot' in sys.argv:
    print('Now rendering a plot of the relation graph...')
    session.database.plot()
