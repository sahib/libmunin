#!/usr/bin/env python
# encoding: utf-8


# Stdlib:
import abc

# External
from bidict import bidict


class Provider:
    """
    A Provider transforms (i.e normalizes) a input value

    Provider Protocol:

        A concrete Provider is required to have these functions:

            ``process()``:

                Takes input values and returns a list of output values
                or None on failure.

        A concrete Provider may have these functions:

            ``reverse()``:

                The method that is able to do the transformation.
                It takes a list of output values and returns a list of
                input values, or None on failure.
        """
    __metaclass__ = abc.ABCMeta

    def __init__(self, compress=False):
        """Create a new Provider with the following attributes:

        :param compress: Deduplicate data?
        """
        self.compress = compress
        if compress:
            self._store = bidict()
            self._last_id = 0

    def __or__(self, other_provider):
        """Allows to chain providers by bit oring them.

        Example: ::

            >>> WordlistProvider() | StemProvider()
            CompositeProvider(WordListProvider_instance, StemProvider_instance)

        If you chain together many providers it is recommended to use only one
        CompositeProvider for speed reasons.
        """
        from munin.provider.composite import CompositeProvider
        return CompositeProvider([self, other_provider])

    def _lookup(self, idx_list):
        return tuple(self._store[:idx] for idx in idx_list)

    def process(self, input_value):
        processed_value = self.do_process(input_value)
        if self.compress:
            if input_value in self._store:
                return (self._store[input_value], )

            self._last_id += 1
            self._store[input_value] = self._last_id
            return (self._last_id, )

        return processed_value

    @abc.abstractmethod
    def do_process(self, input_value):
        # Default Implementations will only passthrough the value.
        if isinstance(input_value, tuple):
            return input_value
        return (input_value, )

###########################################################################
#                             Import Aliases                              #
###########################################################################

from munin.provider.genre import GenreTreeProvider
from munin.provider.composite import CompositeProvider
from munin.provider.stem import StemProvider, StemProvider
from munin.provider.moodbar import \
    MoodbarProvider, \
    MoodbarMoodFileProvider, \
    MoodbarAudioFileProvider

from munin.provider.bpm import BPMProvider, BPMCachedProvider
from munin.provider.wordlist import WordlistProvider
from munin.provider.normalize import \
    ArtistNormalizeProvider, \
    AlbumNormalizeProvider, \
    TitleNormalizeProvider
