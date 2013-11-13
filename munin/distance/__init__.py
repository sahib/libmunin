#!/usr/bin/env python
# encoding: utf-8

# stdlib:
import datetime
import logging
import abc

# External:
import parse

# Internal:
from munin.utils import SessionMapping, float_cmp

LOGGER = logging.getLogger(__name__)


###########################################################################
#                               Rule Class                                #
###########################################################################


# Parsing is done by the excellent parse module.
RULE_PARSE_PATTERN = parse.compile(
    '{subject} {is_bidir:W}=> {objective} = {distance:f} [{timestamp:ti}]'
)

# Sadly, it does not have the exact same format as std's format()
RULE_WRITE_PATTERN = \
    '{subject} {symbol} {objective} = {distance:+f} [{timestamp}]'


class Rule:
    '''A rule is a mapping from one element to another, associated with a weighting,
    and a timestamp.

    In less theory this means: You can weight certain pairs of input and give
    them manually a rating (or *"distance"*). Even less theory you can for example
    make a rule like this: ::

        >>> Rule.from_string('Hard Rock <=> Metal = 0.25')
        <Rule.from_string("hard rock ==> metal = +0.25 [2013-10-19T13:46:05.215541]")>
    '''
    def __init__(self, subject, objective, distance=0.0, is_bidir=True, timestamp=None):
        '''You usually do not need to call this yourself.

        Use the rules created by other modules or :func:`from_string()`
        '''
        # Take the current time if not
        self._timestamp = timestamp or datetime.datetime.today()
        self._given, self._objective = subject, objective
        self._distance, self._is_bidir = distance, is_bidir

    @staticmethod
    def from_string(description):
        '''Converts a string formatted rule to a Rule objective.

        The format goes like this: ::

            "metal <=> rock = 1.0 [2013-10-18T16:22:44.395925]"

        If the format could not be applied, None will be returned.
        The date in square brackets is ISO 8601 encoded.
        '''
        # Silly workaround for allowing rules that do not have a timestamp.
        # We just append the current date as timestamp in square brackets.
        description = description.strip()
        if not description.endswith(']'):
            description += ' [' + datetime.datetime.today().isoformat() + ']'

        result = RULE_PARSE_PATTERN.parse(description)
        if result is not None:
            result.named['is_bidir'] = (result.named['is_bidir'] == '<')
            return Rule(**result.named)
        else:
            LOGGER.warning('Unable to parse rule: ' + description)

    def format_rule(self):
        '''Format the rule in a way that Rule.from_string can read it.

        Format: ::

            "genre one <=> genre two = distance_as_float [Timestamp]"

        Example: ::

            "metal <=> rock = 1.0 [2013-10-18T16:22:44.395925]"
        '''
        return RULE_WRITE_PATTERN.format(
            subject=self.subject, symbol='<=>' if self.is_bidir else '==>',
            objective=self.objective, distance=self.distance,
            timestamp=self.timestamp.isoformat()
        )
    timestamp = property(
            lambda self: self._timestamp,
            doc='Return a :class:`datetime.datetime` when the rule was created.'
    )

    subject = property(
            lambda self: self._given,
            doc='The predicate of the rule (The *"rock"* in ``"rock => metal"``)'
    )

    objective = property(
            lambda self: self._objective,
            doc='The objective of the rule (The *"metal"* in ``"rock => metal"``)'
    )

    distance = property(
            lambda self: self._distance,
            doc='The distance of the rule (1.0 = bad association, 0.0 = good one)'
    )

    is_bidir = property(
        lambda self: self._is_bidir,
        doc='True if the rule is bidirectional (works in both ways)'
    )

    def __repr__(self):
        return '<Rule.from_string("' + self.format_rule() + '")>'


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

    ##########################
    #  Rules Implementation  #
    ##########################

    def format_rules(self):
        '''Return a string with a list of rules.
        '''
        return '\n'.join(rule.format_rule() for rule in self.rule_items())

    def add_rule(self, subject, objective, distance=0.0, is_bidir=True):
        '''Add a new rule with a subject predicate and a objective.

        The rule will be saved and instead of computing the result between
        those two elements the supplied distance will be used.

        If the rule shall work in both ways you can set is_bidir to True.
        Raises a ValueError when subject and objective is the same (which is silly).
        '''
        if subject == objective:
            raise ValueError(
                'Selfmapped rules do not make sense: {a} ==> {a}'.format(
                    a=subject
                )
            )

        rule = Rule(subject, objective, distance, is_bidir)
        self._rules.setdefault(subject, {})[objective] = rule
        if is_bidir:
            self._rules.setdefault(objective, {})[subject] = rule

    def remove_single_rule(self, subject, objective, is_bidir=True):
        '''Remove a single rule determined by subject and objective.

        If is_bidir is True, also the swapped variant will be deleted.
        Will raise a KeyError if the rule does not exist.
        '''
        section = self._rules.get(subject)
        if section is not None:
            del section[objective]
            if len(section) is 0:
                del self._rules[subject]

        if is_bidir:
            # Swap arguments:
            self.remove_single_rule(objective, subject, is_bidir=False)

    def rule_items(self):
        'Return a set of all known rules specific to this DistanceFunction'
        def _iterator():
            for subject, objective_dict in self._rules.items():
                for objective, rule in objective_dict.items():
                    yield rule
        return set(_iterator())

    def lookup_rule(self, subject, objective, is_bidir=True):
        '''Lookup a single rule.

        :returns: The distance initially supplied with the rule.
        '''
        section = self._rules.get(subject)
        if section is not None:
            return section.get(objective)

        if is_bidir:
            return self.lookup_rule(objective, subject, is_bidir=False)

    def save_rules(self, rule_file):
        '''Aboslute path to the rule file.'''
        with open(rule_file, 'w') as handle:
            handle.write(self.format_rules())

    def load_rules_from_file(self, rules_file, reset=True):
        if reset:
            self._rules = {}

        with open(rule_file, 'r') as handle:
            for line in handle:
                rule = Rule.from_string(line)
                self.add_rule(rule.subject, rule.objective, rule.distance, rule.is_bidir)

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
        self._distance = self.weight()

    def __eq__(self, other):
        return float_cmp(self.distance, other.distance)

    def __lt__(self, other):
        return self.distance < other.distance

    def __repr__(self):
        return '~{d:f}'.format(d=self.distance)

    def __hash__(self):
        return hash(self._distance)

    @property
    def distance(self):
        'Return the condensed and weighted distance'
        return self._distance

    def weight(self):
        '''Compute the weighted distance from all seperate sources.

        This is public for testing and validation.
        '''
        dist_sum = 0.0

        # Collect a list of (weight, dists) and the max weight.
        for key, dist in self.items():
            # Do not insert not calculated distances.
            weight = self._session.weight_for_key(key)
            dist_sum += (dist if dist is not None else 1.0) * weight

        # Return the average distance with weight applied.
        return dist_sum / self._session.weight_sum

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
    from munin.provider import DirectProvider

    class DistanceFunctionTest(unittest.TestCase):
        def test_simple(self):
            dist = DistanceFunction(provider=DirectProvider(), name='test')
            dist.add_rule('rock', 'metal')
            self.assertTrue(len(dist.rule_items()) is 1)

            with self.assertRaises(ValueError):
                dist.add_rule('rock', 'rock')

            dist.add_rule('pop', 'rock', is_bidir=False)
            self.assertTrue(len(dist.rule_items()) is 2)
            self.assertTrue(dist.lookup_rule('pop', 'rock').objective == 'rock')
            self.assertEqual(dist.lookup_rule('rock', 'pop'), None)

            rule = dist.lookup_rule('pop', 'rock')
            self.assertEqual(
                    rule.format_rule(),
                    Rule.from_string(rule.format_rule()).format_rule()
            )

            # Test if the ommitted timestamp works fine:
            self.assertEqual(
                Rule.from_string('berta blues ==> hardcore herbert = 1.0').subject,
                'berta blues'
            )

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
            self.assertTrue(float_cmp(dist.weight(), 1.0))

            # Compute it manually:
            dist = Distance(self._session, {'genre': 0.5, 'random': 0.1})
            self.assertTrue(float_cmp(dist.weight(), (0.5 * 0.5 + 0.1 * 0.1) / 0.6))

    unittest.main()
