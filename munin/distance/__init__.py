#!/usr/bin/env python
# encoding: utf-8

import time


class Rule:
    def __init__(self, given, cons, distance=0.0, is_bidir=True):
        # Take the current time if not
        self._timestamp = time.time()
        self._given, self._cons = given, cons
        self._distance, self._is_bidir = distance, is_bidir

    timestamp = property(
            lambda self: self._timestamp,
            doc='Return a Unix timestamp when the rule was created.'
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


# TODO: Rename it to DistanceCalculator?
class Distance:
    def __init__(self):
        # TODO: Load from/save to file.
        # TODO: Implement list rules. (does this even make sense?)
        self._rules = {}

    def __repr__(self):
        'Simple table of rules'
        lines = []
        for rule in self.rule_items():
            line = '{0:<8} {1} {2:<8} [{3:+f}] ({4})'.format(
                rule.given, '<=>' if rule.is_bidir else '==>', rule.cons,
                rule.distance, time=time.asctime(time.localtime(rule.timestamp))
            )
            lines.append(line)
        return '\n'.join(lines)

    ##########################
    #  Rules Implementation  #
    ##########################

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
        'Return a set of all known rules specific to this Distance'
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

    ##############################
    #  Interface for subclasses  #
    ##############################

    def calculate_distance(self, list_a, list_b):
        # Default to max. diversity:
        return 1.0


if __name__ == '__main__':
    import unittest

    # TODO: Finish these.
    class DistanceTest(unittest.TestCase):
        def test_simple(self):
            dist = Distance()
            dist.add_rule('rock', 'metal')

            with self.assertRaises(ValueError):
                dist.add_rule('rock', 'rock')

            dist.add_rule('pop', 'rock', is_bidir=False)
            print(dist)
            print(dist.lookup_rule('pop', 'rock'))
            print(dist.lookup_rule('rock', 'pop'))

    unittest.main()
