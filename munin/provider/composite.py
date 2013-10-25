#!/usr/bin/env python
# encoding: utf-8

'''
**Usage Example:** ::

    >>> from munin.provider.composite import CompositeProvider
    >>> from munin.provider.attic import AtticProvider
    >>> # Create a provider that first matches a genre to the Tree,
    >>> # then cache it with the Attic Provider.
    >>> prov = CompositeProvider([
    ...     GenreTreeProvider(quality='all'),
    ...     AtticProvider()
    ... ])
    >>> # ... use ``prov`` in the Attribute Mask as usual.
'''


from munin.provider import DirectProvider


class CompositeProvider(DirectProvider):
    '''A Provider that is able to chain several Provider into one.

    This is often useful when one has to do some normalization first,
    but afterwards the input must be cached or matched against a table index.

    If no providers are given this acts like (a slower variant) of DirectProvider.
    '''
    def __init__(self, provider_list):
        '''Creates a proivder that applies subproviders in a certain order to it's input.

        :param provider_list: A ordered list of provider objects.
        '''
        DirectProvider.__init__(self, 'Composite({provs})'.format(
            provs=' | '.join(prov.get_name() for prov in provider_list)
        ))

    def process(self, input_value):
        'Apply all providers on the input_value'
        result = input_value
        for provider in provider_list:
            # Loop-prevention:
            if provider is not self:
                r_last = provider.process(input_value)
                result = r_last if r_last is not None else result
        return result
