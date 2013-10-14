#!/usr/bin/env python
# encoding: utf-8


class Provider:
    def __init__(self, name, doc=None):
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value


class DirectProvider(Provider):
    '''Direct Providers usually get a single input value and process them
    in some way (for example normalize them). Usually they have no sideeffects.
    '''
    def process(self, input_value):
        # Default Implementations will only passthrough the value.
        return input_value


class IndirectProvider(Provider):
    '''Indirect providers receive external data or configuration, for example
    a path to a file, and create a value from these.
    '''
    def process(self, *args, **kwargs):
        # Default Implementation does not know anything.
        # Therefore None is the only valid value.
        return None
