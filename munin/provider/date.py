#!/usr/bin/env python
# encoding: utf-8

"""
Overview
--------

Try to parse a date string into a year.

This makes use of the ``magicdate`` module:

    https://pypi.python.org/pypi/magicdate/0.1.3

Example Usage
-------------

.. code-block:: python

    >>> from munin.provider.date import DateProvider
    >>> prov = DateProvider()
    >>> prov.do_process('2012')
    2012
    >>> prov.do_process('2011-12-12')
    2011

Reference
---------

.. autoclass:: munin.provider.date.DateProvider
    :members:
"""

# Internal
from munin.provider import Provider

# External
import magicdate


class DateProvider(Provider):
    """Try to parse an arbitary date string into a year."""
    def do_process(self, input_value):
        if isinstance(input_value, tuple):
            input_value = input_value[0]
        try:
            return (int(input_value), )
        except ValueError:
            try:
                datetime = magicdate.magicdate(input_value)
                return (datetime.year, )
            except:
                return None


if __name__ == '__main__':
    import unittest

    class DateProviderTest(unittest.TestCase):
        def test_date(self):
            prov = DateProvider()
            self.assertEqual(prov.do_process('2012'), (2012, ))
            self.assertEqual(prov.do_process('2012-12-12'), (2012, ))
            self.assertEqual(prov.do_process('2012-20-20'), None)

    unittest.main()
