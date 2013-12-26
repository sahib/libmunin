#!/usr/bin/env python
# encoding: utf-8

"""
Overview
========

This provider is able to analyze an audio file path in order to find the
average beats-per-minute rate.

**Usage Example:**

.. code-block:: python

    >>> from munin.provider import BPMProvider
    >>> p = BPMProvider()
    >>> p.do_process('/tmp/some_file.mp3')
    (123.456, )  # beats per minute

The potential Information you can get from this is: Songs of different genre
often have differente tempi, therefore are less similar. This is no rule of course.

**Problems to consider:**

    * Noisy Live-data often gets high BPM counts
    * Speed-Metal (as an example) ranges in the same

**Prerequisites:**

To function properly this poorly implemented provider needs two external utils:

    * http://sox.sourceforge.net/
    * http://www.pogo.org.uk/~mark/bpm-tools/

Reference
=========
"""


import os
import pipes
import shutil
import subprocess

import logging
LOGGER = logging.getLogger(__name__)

# Fix for Python 3.2
try:
    from subprocess import DEVNULL
except ImportError:
    subprocess.DEVNULL = open(os.devnull, 'w')

from munin.provider import Provider
from munin.helper import float_cmp


def check_for_bpmtools():
    """Check if all required tools are installed for this Provider.

        - ``bpm-tools`` (``bpm`` executable)
        - ``sox`` (``sox`` executable)

    :returns: True if both binaries were found.
    """
    return shutil.which('bpm') and shutil.which('sox')


BPM_COMMAND = \
    "sox -v 1.0 {path} -t raw -r 44100 -e float -c 1 - | bpm -m 60 -x 350"


class BPMProvider(Provider):
    """A Beats-per-minute provider.

    Currently, this is stupidly implemented as a call to an external util:

    .. code-block:: bash

        $ sox -v 1.0 path -t raw -r 44100 -e float -c 1 - | bpm -m 60 -x 350

    More Information on beats per minute:

        http://en.wikipedia.org/wiki/Tempo#Beats_per_minute
    """
    def do_process(self, audio_path):
        try:
            stdout = subprocess.check_output(
                    BPM_COMMAND.format(path=pipes.quote(audio_path)),
                    shell=True, stderr=DEVNULL
            )
            converted = float(stdout.decode('utf-8').strip())

            # Check if the maximum value is reached (which usually means an error)
            if float_cmp(converted, 350):
                return None

            return (converted, )
        except subprocess.CalledProcessError as err:
            LOGGER.debug('"{cmd}" failed with {e}'.format(cmd=err.cmd, e=err.returncode))
        except UnicodeDecodeError:
            LOGGER.debug('could not convert input to valid utf-8')

        return None


class BPMCachedProvider(BPMProvider):
    """Same as :class:`BPMProvider`, but adds a caching layer.

    A .bpm file with the calculated value will be stored along the audio file,
    and the same place will be checked before actually calculating it.
    """
    def __init__(self, cache_invalid=False, **kwargs):
        """
        :param cache_invalid: Also cache invalid results of failed calculations?
        """
        Provider.__init__(self, **kwargs)
        self._cache_invalid = cache_invalid

    def do_process(self, audio_path):
        try:
            cache_path = audio_path + '.bpm'
            if os.access(cache_path, os.R_OK):
                with open(cache_path, 'r') as handle:
                    content = handle.read()
                    if content:
                        LOGGER.debug('bpm for {} was cached.'.format(audio_path))
                        return (float(content), )
                    else:

                        return None

            LOGGER.debug('calculating bpm for {}'.format(audio_path))
            bpm = BPMProvider.do_process(self, audio_path)
            if self._cache_invalid or bpm is not None:
                with open(cache_path, 'w') as handle:
                    if bpm is not None:
                        handle.write(str(bpm[0]))
            return bpm
        except OSError:
            pass

        return ()


###########################################################################
#                                  Tests                                  #
###########################################################################


if __name__ == '__main__':
    from sys import argv
    from munin.helper import AudioFileWalker

    if '--cli' in argv:
        try:
            bpms = []
            provider = BPMCachedProvider(cache_invalid=True)
            for audio_path in AudioFileWalker(argv[2]):
                bpm = provider.do_process(audio_path)
                bpms.append((
                    bpm[0] if bpm else 0.0,
                    audio_path
                ))

            for bpm, audio_path in sorted(bpms, key=lambda elem: elem[0]):
                print('{:<10} {}'.format(bpm, audio_path))
        except KeyboardInterrupt:
            pass
