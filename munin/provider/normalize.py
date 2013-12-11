#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
import unicodedata


# Internal:
from munin.provider import Provider


# Providers:
#    WordlistProvider
#    BPMProvider
#    NotInProvider


class UnicodeGlyphProvider(Provider):
    def do_process(self, input_string):
        return (unicodedata.normalize('NFKC', input_string), )
