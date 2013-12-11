#!/usr/bin/env python
# encoding: utf-8

"""
**Usage Example:** ::

    >>> from munin.provider.composite import CompositeProvider
    >>> from munin.provider.stem import LancasterStemProvider
    >>> # Create a provider that first matches a genre to the Tree,
    >>> # then stem it with the StemProvider.
    >>> prov = CompositeProvider([
    ...     GenreTreeProvider(quality='all'),
    ...     LancasterStemProvider()
    ... ])
    >>> # Alternatively:
    >>> GenreTreeProvider(quality='all') | LancasterStemProvider()

"""


from munin.provider import Provider


class CompositeProvider(Provider):
    """A Provider that is able to chain several Provider into one.

    This is often useful when one has to do some normalization first,
    but afterwards the input must be cached or matched against a table index.

    If no providers are given this acts like (a slower variant) of Provider.
    """
    def __init__(self, provider_list, compress=False):
        """Creates a proivder that applies subproviders in a certain order to it's input.

        :param provider_list: A ordered list of provider objects.
        """
        self._provider_list = provider_list
        Provider.__init__(self, compress=compress)

    def reverse(self, output_values):
        """Try to reverse the output_values with all known providers.

        This function will only work in a sensible way if :func:`is_reversible`
        yield `True`.

        .. seealso:: :func:`munin.provider.Provider.reverse`
        """
        for provider in reversed(self._provider_list):
            if hasattr(provider, 'reverse'):
                raise AttributeError('Provider {p} is not reversible'.format(p=provider.name))
            output_values = provider.reverse(output_values)
        return output_values

    def do_process(self, input_value):
        'Apply all providers on the input_value'
        result = input_value
        for provider in self._provider_list:
            # Loop-prevention:
            if provider is not self:
                last = provider.process(result)
                if last is None:
                    break
                result = last
        return result


if __name__ == '__main__':
    import unittest

    class CompositeProviderTests(unittest.TestCase):
        def test_process(self):
            from munin.provider import Provider
            from munin.provider.genre import GenreTreeProvider

            one = GenreTreeProvider()
            two = Provider()
            prv = one | two
            a = prv.process('metalcore')
            self.assertEqual(a, one.process('metalcore'))

    unittest.main()
