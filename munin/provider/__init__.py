#!/usr/bin/env python
# encoding: utf-8


import abc


class Provider:
    '''
    A Provider transforms (i.e normalizes) a input value

    Provider Protocol:

        A concrete Provider is required to have these functions:

            ``process()``:

                Takes input values and returns a list of output values
                or None on failure.

            ``is_reversible``:

                This property should be True if the results returned by
                ``process()`` can be transormed back to the input value.

            ``reverse()``:

                The method that is able to do the transformation.
                It takes a list of output values and returns a list of
                input values, or None on failure.

                This method should also exist even if ``is_reversible``
                is False. In this case the output_value list shall be
                returned.

            Additional each provider should have a settable ``name``
            property for display purpose.
        '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, name='Default Provider', is_reversible=True):
        '''Create a new Provider with the following attributes:

        :param name: A display name for this Provider.
        :param is_reversible: Can the output of ``process()`` reversed by ``reverse()``.
        '''
        self._name = name
        self._is_reversible = is_reversible

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @abc.abstractproperty
    def is_reversible(self):
        'If *True* this provider is reversible via :func:`reverse` (aka **injective**)'
        return self._is_reversible

    @abc.abstractmethod
    def process(self, input_value):
        # Default Implementations will only passthrough the value.
        return (input_value, )

    def reverse(self, output_values):
        '''Reverse the value previously processed by :func:`process`.

        This only works if the :func:`is_reversible` is set, otherwise
        the value will be simply returned. (Which is the default for
        :class:`Provider`).

        .. note::

            It is not required that the return value is the excact input value
            you gave into :func:`process`. It is only required that a value is
            returned that gives the same result when processing it again.

            Example for the :class:`munin.provider.genre.GenreTreeProvider`: ::

                >>> p.process([('Metalcore', )])
                [(82, 1)]
                >>> p.reverse([(82, 1)])
                [('metal core', )]  # Note the space.
                >>> p.process([('metal core', )])
                [(82, 1)]

        :param output_value: A value previously returned from :func:`process`.
        :return: A value similar to the input value you gave into :func:`process`.
        '''
        return tuple(output_values)

###########################################################################
#                             Import Aliases                              #
###########################################################################

from munin.provider.genre import GenreTreeProvider
from munin.provider.attic import AtticProvider
from munin.provider.composite import CompositeProvider
from munin.provider.stem import LancasterStemProvider, SnowballStemProvider
