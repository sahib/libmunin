#!/usr/bin/env python
# encoding: utf-8

# stdlib:
import datetime
import logging
import abc

# Internal:
from munin.utils import SessionMapping, float_cmp

LOGGER = logging.getLogger(__name__)


###########################################################################
#                          DistanceFunction Class                          #
###########################################################################

class DistanceFunction:
    'A **DistanceFunction** calculates a **Distance**'

    __metaclass__ = abc.ABCMeta

    def __init__(self, provider, name='Default', to_reverse=None):
        '''This class is supposed to be overriden, but can also be used
        as fallback.

        .. todo:: Write documentation for rules.

        ``__call__`` is implemented as shortcut to :func:`compute`

        :param provider: Provider to be used to normalize Rules.
        :type provider: instance of :class:`munin.provider.Provider`
        :param name: Name of the DistanceFunction (used for display)
        :type name: String.
        '''
        self._rules = {}
        self._name = name
        self._provider = provider
        self._to_reverse = to_reverse or []

    def __repr__(self):
        'Prints a simple table of rules'
        return '<DistanceFunction rules=' + self.format_rules() + '>'

    def __call__(self, list_a, list_b):
        'Shortcut for :func:`compute`'
        return self.compute(list_a, list_b)

    ##############################
    #  Interface for subclasses  #
    ##############################

    @abc.abstractmethod
    def get_name(self):
        '''Return the name of this DistanceFunction (for display purpose)'''
        return self._name

    @abc.abstractmethod
    def compute(self, list_a, list_b):
        '''Compare both lists with eq by default.

        This goes through both lists and counts the matching elements.
        The lists are sorted in before.

        :return: Number of matches divivded through the max length of both lists.
        '''
        list_a, list_b = self.apply_reverse_both(list_a, list_b)

        # Default to max. diversity:
        n_max = max(len(list_a), len(list_b))
        if n_max is 0:
            return 1.0

        return 1.0 - sum(a == b for a, b in zip(sorted(list_a), sorted(list_b))) / n_max

    ###############
    #  Reversing  #
    ###############

    def apply_reverse_both(self, lefts, rights):
        '''Convienience function that applies :func:`apply_reverse` to both lists.

        :param lefts: A list of input values.
        :param rights: Another list of input values.
        :return: A tuple of two lists.
        '''
        return self.apply_reverse(lefts), self.apply_reverse(rights)

    def apply_reverse(self, input_values):
        '''Apply the ``reverse()`` function of the providers in the ``to_reverse``
        list passed to ``__init__()`` to each value in ``input_values.``
        '''
        if not self._to_reverse:
            return input_values

        return [self.apply_reverse_single(value) for value in input_values]

    def apply_reverse_single(self, single_value):
        for provider in self._to_reverse:
            single_value = provider.reverse((single_value, ))
        return single_value


###########################################################################
#                             Distance Class                              #
###########################################################################


class Distance(SessionMapping):
    __slots__ = ('_distance')

    'A **Distance** between two Songs.'
    def __init__(self, session, dist_dict):
        '''A Distance saves the distances created by providers and boil it down
        to a single distance float by weighting the individual distances of each
        song's attributes and building the average of it.

        :param session: The session this distance belongs to. Only valid in it.
        :type session: Instance of :class:`munin.session.Session`
        :param dist_dict: A mapping to read the distance values from.
        :type dist_dict: mapping<str, float>
        '''
        # Use only a list internally to save the values.
        # Keys are stored shared in the Session objective.
        SessionMapping.__init__(self, session, dist_dict, default_value=None)
        self._distance = session._weight(dist_dict)

    def __eq__(self, other):
        return float_cmp(self.distance, other.distance)

    def __lt__(self, other):
        return self.distance < other.distance

    def __repr__(self):
        return '~{d:f}'.format(d=self.distance)

    def __hash__(self):
        return hash(self._distance)

    def __invert__(self):
        return 1.0 - self.distance

    @property
    def distance(self):
        'Return the condensed and weighted distance'
        return self._distance

###########################################################################
#                             Import Aliases                              #
###########################################################################

from munin.distance.genre import GenreTreeDistance

###########################################################################
#                               Unit tests                                #
###########################################################################

if __name__ == '__main__':
    import unittest
    from munin.session import Session
    from munin.provider import Provider

    class DistanceFunctionTest(unittest.TestCase):
        def test_apply(self):
            from munin.provider.attic import AtticProvider
            provider = AtticProvider()
            dist = DistanceFunction(
                    provider=provider,
                    to_reverse=[provider],
                    name='test'
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
