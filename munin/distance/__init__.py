#!/usr/bin/env python
# encoding: utf-8

import datetime
import logging
import parse
LOGGER = logging.getLogger('libmunin')


# Parsing is done by the excellent parse module.
RULE_PARSE_PATTERN = parse.compile(
    '{given} {is_bidir:W}=> {cons} = {distance:f} [{timestamp:ti}]'
)

# Sadly, it does not have the exact same format as std's format()
RULE_WRITE_PATTERN = \
    '{given} {symbol} {cons} = {distance:+f} [{timestamp}]'


class Rule:
    '''A rule is a mapping from one element to another, associated with a weighting,
    and a timestamp.

    In less theory this means: You can weight certain pairs of input and give
    them manually a rating (or "distance"). Even less theory you can for example
    make a rule like this: ::

        >>> Rule.from_string('Hard Rock <=> Metal = 0.25')
        <Rule.from_string("hard rock ==> metal = +0.25 [2013-10-19T13:46:05.215541]")>
    '''
    def __init__(self, given, cons, distance=0.0, is_bidir=True, timestamp=None):
        '''You usually do not need to call this yourself.

        Use the rules created by other modules or Rule.from_string()
        '''
        # Take the current time if not
        self._timestamp = timestamp or datetime.datetime.today()
        self._given, self._cons = given, cons
        self._distance, self._is_bidir = distance, is_bidir

    @staticmethod
    def from_string(description):
        '''Converts a string formatted rule to a Rule object.

        The format goes like this:

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
        return RULE_WRITE_PATTERN.format(
            given=self.given, symbol='<=>' if self.is_bidir else '==>',
            cons=self.cons, distance=self.distance,
            timestamp=self.timestamp.isoformat()
        )

    timestamp = property(
            lambda self: self._timestamp,
            doc='Return a datetime when the rule was created.'
    )

    given = property(
            lambda self: self._given,
            doc='The predicate of the rule (The "rock" in "rock" => "metal")'
    )

    cons = property(
            lambda self: self._cons,
            doc='The consequence of the rule (The "metal" in "rock" => "metal")'
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


class DistanceMeasure:
    def __init__(self, name):
        self._rules = {}
        self._name = name

    def __repr__(self):
        'Prints a simple table of rules'
        return self.format_rules()

    ##########################
    #  Rules Implementation  #
    ##########################

    def format_rules(self):
        return '\n'.join(rule.format_rule() for rule in self.rule_items())

    def add_rule(self, given, cons, distance=0.0, is_bidir=True):
        '''Add a new rule with a given predicate and a consequence.

        The rule will be saved and instead of computing the result between
        those two elements the supplied distance will be used.

        If the rule shall work in both ways you can set is_bidir to True.
        Raises a ValueError when given and cons is the same (which is silly).
        '''
        if given == cons:
            raise ValueError(
                'Selfmapped rules do not make sense: {a} ==> {a}'.format(
                    a=given
                )
            )

        rule = Rule(given, cons, distance, is_bidir)
        self._rules.setdefault(given, {})[cons] = rule
        if is_bidir:
            self._rules.setdefault(cons, {})[given] = rule

    def remove_single_rule(self, given, cons, is_bidir=True):
        '''Remove a single rule determined by given and cons.

        If is_bidir is True, also the swapped variant will be deleted.
        Will raise a KeyError if the rule does not exist.
        '''
        section = self._rules.get(given)
        if section is not None:
            del section[cons]
            if len(section) is 0:
                del self._rules[given]

        if is_bidir:
            # Swap arguments:
            self.remove_single_rule(cons, given, is_bidir=False)

    def rule_items(self):
        'Return a set of all known rules specific to this DistanceMeasure'
        def _iterator():
            for given, cons_dict in self._rules.items():
                for cons, rule in cons_dict.items():
                    yield rule
        return set(_iterator())

    def lookup_rule(self, given, cons, is_bidir=True):
        '''Lookup a single rule.

        :returns: The distance initially supplied with the rule.
        '''
        section = self._rules.get(given)
        if section is not None:
            return section.get(cons)

        if is_bidir:
            return self.lookup_rule(cons, given, is_bidir=False)

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
                self.add_rule(rule.given, rule.cons, rule.distance, rule.is_bidir)

    ##############################
    #  Interface for subclasses  #
    ##############################

    def get_name(self):
        return self._name

    def calculate_distance(self, list_a, list_b):
        # Default to max. diversity:
        return 1.0


if __name__ == '__main__':
    import unittest

    class DistanceTest(unittest.TestCase):
        def test_simple(self):
            dist = DistanceMeasure(name='test')
            dist.add_rule('rock', 'metal')
            self.assertTrue(len(dist.rule_items()) is 1)

            with self.assertRaises(ValueError):
                dist.add_rule('rock', 'rock')

            dist.add_rule('pop', 'rock', is_bidir=False)
            self.assertTrue(len(dist.rule_items()) is 2)
            self.assertTrue(dist.lookup_rule('pop', 'rock').cons == 'rock')
            self.assertEqual(dist.lookup_rule('rock', 'pop'), None)

            rule = dist.lookup_rule('pop', 'rock')
            self.assertEqual(
                    rule.format_rule(),
                    Rule.from_string(rule.format_rule()).format_rule()
            )

            # Test if the ommitted timestamp works fine:
            self.assertEqual(
                Rule.from_string('berta blues ==> hardcore herbert = 1.0').given,
                'berta blues'
            )

    unittest.main()
