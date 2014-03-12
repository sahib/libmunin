#!/usr/bin/env python
# encoding: utf-8

# stdlib:
import logging
import abc

# Internal:
from munin.helper import SessionMapping, float_cmp

LOGGER = logging.getLogger(__name__)


###########################################################################
#                          DistanceFunction Class                          #
###########################################################################

class DistanceFunction:
    'A **DistanceFunction** calculates a **Distance**'

    __metaclass__ = abc.ABCMeta

    def __init__(self, provider=None):
        """This class is supposed to be overriden, but can also be used
        as fallback.

        ``__call__`` is implemented as shortcut to :func:`compute`

        :type provider: instance of :class:`munin.provider.Provider`
        :param name: Name of the DistanceFunction (used for display)
        :type name: String.
        """
        self._provider = provider

    def __call__(self, list_a, list_b):
        'Shortcut for :func:`compute`'
        return self.compute(list_a, list_b)

    def compute(self, lefts, rights):
        if self._provider is not None and self._provider.compress:
            lefts = self._provider._lookup(lefts)
            rights = self._provider._lookup(rights)

        return self.do_compute(lefts, rights)

    ##############################
    #  Interface for subclasses  #
    ##############################

    @abc.abstractmethod
    def do_compute(self, list_a, list_b):
        """Compare both lists with eq by default.

        This goes through both lists and counts the matching elements at the same index.

        :return: Number of matches divivded through the max length of both lists.
        """
        # Default to max. diversity:
        n_max = max(len(list_a), len(list_b))
        if n_max is 0:
            return 1.0

        return 1.0 - sum(a == b for a, b in zip(list_a, list_b)) / n_max


###########################################################################
#                             Distance Class                              #
###########################################################################


class Distance(SessionMapping):
    __slots__ = ('distance')

    'A **Distance** between two Songs.'
    def __init__(self, session, dist_dict):
        """A Distance saves the distances created by providers and boil it down
        to a single distance float by weighting the individual distances of each
        song's attributes and building the average of it.

        :param session: The session this distance belongs to. Only valid in it.
        :type session: Instance of :class:`munin.session.Session`
        :param dist_dict: A mapping to read the distance values from.
        :type dist_dict: mapping<str, float>
        """
        # Use only a list internally to save the values.
        # Keys are stored shared in the Session objective.
        SessionMapping.__init__(self, session, dist_dict, default_value=None)
        self.distance = session._weight(dist_dict)

    def __eq__(self, other):
        return float_cmp(self.distance, other.distance)

    def __lt__(self, other):
        return self.distance < other.distance

    def __repr__(self):
        return '~{d:f}'.format(d=self.distance)

    def __hash__(self):
        return hash(self.distance)

    def __invert__(self):
        return 1.0 - self.distance

    @staticmethod
    def make_dummy(session):
        return Distance(
            session,
            {key: 0.0 for key in session._mask.keys()}
        )


###########################################################################
#                             Import Aliases                              #
###########################################################################

from munin.distance.bpm import BPMDistance
from munin.distance.date import DateDistance
from munin.distance.genre import GenreTreeDistance, GenreTreeAvgDistance
from munin.distance.rating import RatingDistance
from munin.distance.moodbar import MoodbarDistance
from munin.distance.keywords import KeywordsDistance
from munin.distance.wordlist import WordlistDistance
from munin.distance.levenshtein import LevenshteinDistance

###########################################################################
#                               Unit tests                                #
###########################################################################

if __name__ == '__main__':
    import unittest
    from munin.session import Session
    from munin.provider import Provider

    class DistanceFunctionTest(unittest.TestCase):
        def test_apply(self):
            provider = Provider(compress=True)
            dist = DistanceFunction(
                provider=provider
            )

            a = provider.process('Akrea')
            b = provider.process('Berta')
            c = provider.process('akrea'.capitalize())

            self.assertEqual(a, (1, ))
            self.assertEqual(b, (2, ))
            self.assertEqual(c, (1, ))

            self.assertAlmostEqual(dist.compute(a, b), 1.0)
            self.assertAlmostEqual(dist.compute(a, c), 0.0)
            self.assertAlmostEqual(dist.compute([], []), 1.0)
            self.assertAlmostEqual(
                    dist.compute(a + b, c),
                    0.5
            )

    class DistanceTest(unittest.TestCase):
        def setUp(self):
            self._session = Session('test', {
                'genre': (None, None, 0.5),
                'random': (None, None, 0.1)
            })

        def test_weight(self):
            dist = Distance(self._session, {'genre': 1.0})
            self.assertAlmostEqual(dist.distance, 1.0)
            dist = Distance(self._session, {'random': 1.0})
            self.assertAlmostEqual(dist.distance, 1.0)
            dist = Distance(self._session, {'genre': 1.0, 'random': 1.0})
            self.assertAlmostEqual(dist.distance, 1.0)
            dist = Distance(self._session, {'genre': 1.0, 'random': 0.0})
            self.assertAlmostEqual(dist.distance, 5 / 6)
            dist = Distance(self._session, {'genre': 0.0, 'random': 0.0})
            self.assertAlmostEqual(dist.distance, 0.0)

            # Compute it manually:
            dist = Distance(self._session, {'genre': 0.5, 'random': 0.1})
            self.assertTrue(float_cmp(dist.distance, (0.5 * 0.5 + 0.1 * 0.1) / 0.6))

    unittest.main()
