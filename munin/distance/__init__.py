#!/usr/bin/env python
# encoding: utf-8

import time


class Rule:
    def __init__(self, base, deduction, distance=0.0, is_bidir=True, timestamp=None):
        self.timestamp = time.time() if timestamp is None else timestamp
        self.base, self.deduction = base, deduction
        self.distance, self.is_bidir = distance, is_bidir


class Distance:
    def __init__(self):
        # TODO: Load from/save to file.
        # TODO: Implement list rules. (does this even make sense?)
        self._rules = {}
        self._inv_rules = {}

    def add_single_rule(self, base, deduction, distance=0.0, is_bidir=True, timestamp=None):
        if base == deduction:
            raise ValueError(
                'Selfmapped rules do not make sense: {a} ==> {a}'.format(
                    a=base
                )
            )

        rule = Rule(base, deduction, distance, is_bidir, timestamp)
        self._rules[base] = rule
        if is_bidir is True:
            self._inv_rules[deduction] = rule

    def remove_single_rule(self, base, deduction=None, is_bidir=True):
        del self._inv_rules[base]
        if is_bidir is True and deduction is not None:
            del self._inv_rules[deduction]

    def __repr__(self):
        lines = []
        for rule in self.rules():
            lines.append(
                '{base:<8} {symbol} {ded:<8} [{dist:+f}] ({time})'.format(
                    base=rule.base,
                    symbol='<=>' if rule.is_bidir else '==>',
                    ded=rule.deduction,
                    dist=rule.distance,
                    time=time.asctime(time.localtime(rule.timestamp))
                )
            )
        return '\n'.join(lines)

    def rules(self):
        return self._rules.values()

    def check_single_rule(self, elem_a, elem_b):
        rule = self._rules.get(elem_a, self._inv_rules.get(elem_a))
        if rule is not None and rule.deduction == elem_b:
            return rule

        rule = self._rules.get(elem_b, self._inv_rules.get(elem_b))
        if rule is not None and rule.deduction == elem_a:
            return rule

    def calculate_distance(self, list_a, list_b):
        # Default to max. diversity:
        return 1.0


if __name__ == '__main__':
    import unittest

    class DistanceTest(unittest.TestCase):
        def test_simple(self):
            dist = Distance()
            dist.add_single_rule('rock', 'metal')

            with self.assertRaises(ValueError):
                dist.add_single_rule('rock', 'rock')

            dist.add_single_rule('pop', 'rock', is_bidir=False)
            print(dist)

    unittest.main()
