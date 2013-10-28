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
        self._provider_list = provider_list
        DirectProvider.__init__(self, 'Composite({provs})'.format(
            provs=' | '.join(prov.get_name() for prov in provider_list),
            is_reversible=True
        ))

    def reverse(self, output_values):
        '''Try to reverse the output_values with all providers that support that.

        If a provider is encounter that has is_reversible set to False we stop
        and return the intermediate result as best match.

        (Therefore this function is not guaranteed to be fully reversible).
        '''
        for provider in self._provider_list:
            if not provider.is_reversible:
                break
            output_values = provider.reverse(output_values)
        return output_values

    def process(self, input_value):
        'Apply all providers on the input_value'
        result = input_value
        for provider in self._provider_list:
            # Loop-prevention:
            if provider is not self:
                r_last = provider.process(input_value)
                result = r_last if r_last is not None else result
        return result

if __name__ == '__main__':
    import unittest

    class CompositeProviderTests(unittest.TestCase):
        def test_process(self):
            pass
            # TODO: Write tests.

    unittest.main()
