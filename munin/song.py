#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from bisect import bisect, insort
from collections import Hashable
from logging import getLogger
LOGGER = getLogger(__name__)

# Internal:
from munin.distance import Distance
from munin.utils import SessionMapping, float_cmp


class Song(SessionMapping, Hashable):
    # Note: Use __slots__ (sys.getsizeof will report even more memory, but pympler less)
    __slots__ = ('_distances', '_max_distance', '_max_neighbors', '_hash', '_confidence', 'uid')
    '''
    **Overview**

    A song is a readonly mapping of keys to values (like a readonly dict).

    The keys will depend on the attribute mask in the session.
    The values will be passed as value_dict to the constructor.
    Keys that are no in value_dict, but in the attribute_mask (therefore valid)
    will return the default_value passed (usually that is None).

    Internally a list is used to store the values, leaving the keys in the
    Session objects - for many instances this saves a considerable amount
    of memory.

    .. todo:: Make some numbers up to prove this :-)

    **Reference**
    '''
    def __init__(self, session, value_dict, max_neighbors=100, max_distance=0.999, default_value=None):
        '''Creates a Song (a set of attributes) that behaves like a dictionary:

        :param session: A Session objective (the session this song belongs to)
        :type session: :class:`munin.session.Session`
        :param value_dict: A mapping from the keys to the values you want to set.
        :type value_dict: Mapping
        :param default_value: The value to be returned for valid but unset keys.
        :param max_neighbors: max. numbers of neighbor-distances to save.
        :type neighbor: positive int
        :param max_distance: The minimal distance for :func:`distance_add` -
                             You should try to keep this small (i.e. to only
                             filter 1.0 distances)
        :type max_distance: float
        '''
        # Make sure the list is as long as the attribute_mask
        SessionMapping.__init__(
                self, session,
                input_dict=value_dict,
                default_value=default_value
        )
        self._distances = {}

        # Settings:
        self._max_neighbors = max_neighbors
        self._max_distance = max_distance

        # Update hash on creation
        self._update_hash()

        self.uid = None

    #######################
    #  Other convinience  #
    #######################

    def __hash__(self):
        return self._hash

    def __repr__(self):
        return '<Song(values={val}, distances={dst})>'.format(
                val=self._store,
                dst={hash(song): val for song, val in self._distances.items()}
        )

    ############################
    #  Distance Relations API  #
    ############################

    def distance_compute(self, other_song):
        '''Compute the distance to another song.

        This is a method of :class:`Song` and not a static method for convinience.
        If you need a static method do this: ``Song.distance_compute(s1, s2)``.

        :param other_song: a :class:`munin.song.Song`
        :returns: A :class:`munin.distance.Distance` with according weighting.
        '''
        distance_dict = {}
        common_keys = set(self.keys()) & set(other_song.keys())
        for key in common_keys:
            distance_func = self._session.distance_function_for_key(key)
            distance_dict[key] = distance_func(
                    self[key],
                    other_song[key]
            )
        return Distance(self._session, distance_dict)

    def distance_add(self, other_song, distance, bidir=True):
        '''Add a relation to ``other_song`` with a certain distance.

        .. warning::

            This function has linear complexity since it needs to find the
            worst element in case of a deletion.

        :param other_song: The song to add a relation to. Will also add a
                           relation in other_song to self with same Distance.
        :type other_song: :class:`munin.song.Song`
        :param distance: The Distance to add to the "edge".
        :type distance: :class:`munin.distance.Distance`
        :param bidir: If *True* also add the relation to *other_song*.
        :type bidir: bool
        :returns: *False* if the song was not added because of a bad distance.
                  *True* in any other case.
        '''
        added = False
        if other_song is self:
            return True

        if distance.distance <= self._max_distance:
            # Check if we still have room left
            if self._max_neighbors < len(self._distances):
                # Find the worst song in the dictionary
                worst_song, worst_dist = max(self._distances.items(), key=lambda x: x[1])

                if distance < worst_dist:
                    # delete the worst one to make place:
                    self._distances.pop(worst_song)
                    self._distances[other_song] = distance
                    added = True
            else:
                # There's still place left.
                self._distances[other_song] = distance
                added = True

        # Repeat procedure for the other song:
        if bidir is True:
            other_song.distance_add(self, distance, bidir=False)

        return added

    def distance_del(self, other_song):
        '''Delete the relation to ``other_song``

        :raises: A :class:`KeyError` if no such key exists.
        '''
        self._distances.pop(other_song)
        other_song._distances.pop(self)

    def distance_get(self, other_song, default_value=None):
        '''Return the distance to the song ``other_song``

        :param other_song: The song to lookup the relation to.
        :param default_value: The default value to return (default to None)
        :returns: A Distance.
        '''
        if self is other_song:
            return self.distance_compute(self)
        else:
            return self._distances.get(other_song, default_value)

    def distance_iter(self):
        '''Iterate over all distances stored in this song.

        :returns: iterable that yields (song, distance) tuples.
        :rtype: generator
        '''
        return self._distances.items()

    def distance_indirect_iter(self, dist_threshold):
        '''Iterate over the indirect neighbors of this song.

        :returns: an generator that yields one song at a time.
        '''
        for song, dist in self.distance_iter():
            if dist.distance < dist_threshold:
                for ind_song, ind_dist in song.distance_iter():
                    if ind_dist.distance < dist_threshold:
                        yield song

    #################################
    #  Additional helper functions  #
    #################################

    def to_dict(self):
        'Shortcut for ``dict(iter(song))``'
        return dict(iter(song))

    @property
    def confidence(self):
        'Yields a tuple of (filled_values, confidence) for this song'
        return self._confidence

    #############
    #  Private  #
    #############

    def _update_hash(self):
        self._hash = hash(tuple(self._store))


###########################################################################
#                            Ifmain Unittests                             #
###########################################################################

if __name__ == '__main__':
    import unittest
    from munin.session import Session

    class SongTests(unittest.TestCase):
        def setUp(self):
            self._session = Session('test', {
                'genre': (None, None, 0.1),
                'artist': (None, None, 0.1)
            })

        def test_song_basic_mapping(self):
            song = Song(self._session, {
                'genre': 'alpine brutal death metal',
                'artist': 'Herbert'
            })

            self.assertTrue(song.get('artist') == song['artist'] == 'Herbert')
            with self.assertRaises(TypeError):
                del song['genre']

        def test_song_missing_attr(self):
            # This should already fail at creation:
            with self.assertRaises(KeyError):
                song = Song(self._session, {'a': 'b'})

            song = Song(self._session, {'genre': 'berta'})

            with self.assertRaises(KeyError):
                song['berta']

            self.assertEqual(song.get('berta'), song.get('barghl'))

        def test_song_iter(self):
            input_dict = {
                'genre': 'alpine brutal death metal',
                'artist': 'Herbert'
            }

            song = Song(self._session, input_dict)
            self.assertEqual(
                    dict(iter(song)),
                    input_dict
            )

            self.assertEqual(dict(iter(song.items())), input_dict)
            self.assertEqual(set(song.keys()), set(['genre', 'artist']))
            self.assertEqual(
                set(song.values()),
                set(['alpine brutal death metal', 'Herbert'])
            )

        def test_distances(self):
            song_one = Song(self._session, {
                'genre': 'alpine brutal death metal',
                'artist': 'Herbert'
            })
            song_two = Song(self._session, {
                'genre': 'tirolian brutal death metal',
                'artist': 'Gustl'
            })

            # Mock the distance class (so we need no session)
            class DistanceDummy:
                def __init__(self, d):
                    self.distance = d

                def __eq__(self, other):
                    return self.distance == other.distance

                def __lt__(self, other):
                    return self.distance > other.distance

                def __repr__(self):
                    return str(self.distance)

            song_one.distance_add(song_two, DistanceDummy(0.7))
            song_one.distance_add(song_one, DistanceDummy(421))  # this should be clamped to 1
            self.assertEqual(song_one.distance_get(song_one), DistanceDummy(0.0))
            self.assertEqual(song_one.distance_get(song_two), DistanceDummy(0.7))

            # Check if max_distance works correctly
            prev_len = len(song_one._distances)
            song_one.distance_add(song_two, DistanceDummy(1.0))
            self.assertEqual(len(song_one._distances), prev_len)

            # Test "only keep the best songs"
            song_base = Song(self._session, {
                'genre': 0,
                'artist': 0
            })

            N = 200
            for idx in range(1, N + 1):
                song = Song(self._session, {
                    'genre': str(idx),
                    'artist': str(idx)
                })
                song_base.distance_add(song, DistanceDummy(idx / N))

            values = sorted(song_base._distances.items(), key=lambda x: x[1])
            self.assertEqual(values[+0][1].distance, (N - 1) / N)
            self.assertEqual(values[-1][1].distance, (N - 100 - 1) / N)

    unittest.main()
