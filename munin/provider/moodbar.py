#!/usr/bin/env python
# encoding: utf-8

"""
Overview
========

A moodbar is a color representation of an audio file, where the red represents
the low frequencies, green the mids and blue the high ones.

Per audio file 1000 RGB Triples are sampled.

Sometimes individual instruments can be recognized by their color, the combination
of E-Guitar and Drums are often found to be turquoise.

Since the moodbar does not really represent the mood information it should
be rather called ``freqbar``. But it was decided to stay with the authors
naming choice.

You can find more information here:

    * http://en.wikipedia.org/wiki/Moodbar

For this provider to work properly you need the moodbar utility installed:

    * http://pwsp.net/~qbob/moodbar-0.1.2.tar.gz

There are 3 different providers in this module:

    * :class:`munin.provider.moodbar.MoodbarProvider`
    * :class:`munin.provider.moodbar.MoodbarMoodFileProvider`
    * :class:`munin.provider.moodbar.MoodbarAudioFileProvider`

**Usage Example:**

.. code-block:: python

    >>> from munin.provider import MoodbarAudioFileProvider
    >>> p = MoodbarAudioFileProvider()
    >>> p.do_process('/tmp/some_file.mp3')
    MoodbarDescription<{
        'red': {
            'histogram': [302, 12, 58, 177, 441, 10]
            'diffsum':   44
        },
        'green': {
            'histogram': [220, 72, 32, 203, 462, 11]
            'diffsum':   33
        },
        'blue': {
            'histogram': [303, 24, 130, 290, 239, 14]
            'diffsum':   32
        },
        'average_minimum': 126,
        'average_maximum': 161,
        'dominant_colors': [
            (187, 238, 238),
            (  0,  34,   0),
            (204, 204, 170),
            (204, 238, 221),
            (  0,  51,   0),
            (204, 221, 187),
            (  0,  34,  17),
            (204, 238, 238),
            (221, 204, 170),
            (  0,  51,  17)
        ]
    }>


Reference
=========
"""


# Stdlib:
import os
import shutil

from collections import Counter, namedtuple, defaultdict
from operator import itemgetter

# Fix for Python 3.2
import subprocess
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'w')

# Internal:
from munin.helper import grouper
from munin.provider import Provider


MoodbarChannel = namedtuple('MoodbarChannel', [
    'histogram', 'diffsum'
])


MoodbarDescription = namedtuple('MoodbarDescription', [
    'channels',
    'average_max', 'average_min',
    'dominant_colors', 'blackness'
])

MoodbarDescription.__repr__ = lambda self: """\
MoodbarDescription<{{
    'red': {{
        'histogram': {hist_r}
        'diffsum':   {diff_r}
    }},
    'green': {{
        'histogram': {hist_g}
        'diffsum':   {diff_g}
    }},
    'blue': {{
        'histogram': {hist_b}
        'diffsum':   {diff_b}
    }},
    'average_minimum': {avg_min},
    'average_maximum': {avg_max},
    'dominant_colors': [
        {dominant_colors}
    ]
}}>
""".format(
    hist_r=self.channels[0].histogram, diff_r=self.channels[0].diffsum,
    hist_g=self.channels[1].histogram, diff_g=self.channels[1].diffsum,
    hist_b=self.channels[2].histogram, diff_b=self.channels[2].diffsum,
    avg_min=self.average_min,
    avg_max=self.average_max,
    dominant_colors=',\n        '.join(
        ['({:>3d}, {:>3d}, {:>3d})'.format(r, g, b) for r, g, b in self.dominant_colors]
    )
)


def check_for_moodbar():
    """Check if all required tools are installed for this Provider.

        - ``moodbar`` (``moodbar`` executable)

    :returns: True if binary was found.
    """
    return bool(shutil.which('moodbar'))


def compute_moodbar_for_file(audio_file, output_file, print_output=False):
    """Call a moodbar process on a certain audio file.

    :param audio_file: Path to an arbitary audio file.
    :param output_file: Path to where the outputfile shall be written.
    :param print_output: Print the output of the moodbar utility?

    :returns: The exit code of the moodbar utility (0 on success).

    """
    stdout, stderr = DEVNULL, DEVNULL
    if print_output:
        stdout, stderr = None, None

    return subprocess.call(
        ['moodbar', audio_file, '-o', output_file],
        stdout=stdout, stderr=stderr
    )


def read_moodbar_values(path):
    """Read a vector of RGB triples from a mood-file (as produced by moodbar).

    :param path: The path where the mood file is located.
    :returns: A list of 1000 RGB Triples.
    """
    with open(path, 'rb') as f:
        return [tuple(rgb) for rgb in grouper(f.read(), n=3)]


def discretize(chan_r, chan_g, chan_b, n=50):
    """Split the list down into blocks and calculate their mean.
    Results in a smaller (original_len / n) list with approximated values.

    :param chan_r: Iterable of the red channel
    :param chan_g: Iterable of the green channel
    :param chan_b: Iterable of the blue channel
    :param n: How big the block size shall be.
    :returns: A generator that yields the new list lazily.
    """
    group_r = grouper(chan_r, n)
    group_g = grouper(chan_g, n)
    group_b = grouper(chan_b, n)
    mean = lambda group: sum(group) / n

    for red, green, blue in zip(group_r, group_g, group_b):
        yield mean(red), mean(green), mean(blue)


def histogram(channel, bin_width=51):
    """Calculate a histogram (i.e. a binned counter of elements) of an iterable.

    :param channel: The channel to consider.
    :param bin_width: The width of each bin (255 / bin_width == 0!)
    :returns: a list of binned values (len = 255 / bin_width)
    """
    counter = defaultdict(int)
    for value in channel:
        counter[(value // bin_width) * bin_width] += 1

    return [counter[key] for key in sorted(counter.keys())]


def extract(vector, chan_idx):
    """Extract a certain channel from an iterable of rgb triples.

    :param vector: The vector with rgb triples.
    :param chan_idx: The idx of the desired channel
    :returns: A flat list with the single values
    """
    f = itemgetter(chan_idx)
    return [f(rgb) for rgb in vector]


def find_dominant_colors(vector, samples, roundoff=34):
    """Find the most dominant colors in the vector.

    :param vector: The vector of rgb triples.
    :param samples: How many dominant colors to find.
    :param roundoff: How much grouping shall be done,
                     high numbers lead to less possible colors.

    :returns: A list with the dominant colors (max len is samples)
              and the percent of black colors as integer.
    """
    blackness_count, result = 0, []
    data = [tuple([v // roundoff * roundoff for v in rgb]) for rgb in vector]

    for color, count in Counter(data).most_common():
        # Do not count very dark colors:
        if all(map(lambda channel: channel <= roundoff, color)):
            blackness_count += count
        else:
            result.append((color, count))

    return result[:samples], int(round(blackness_count / 10))


def process_moodbar(vector, samples=25):
    """Turn a moodbar vector into a :class:`MoodbarDescription`.

    :param vector: The vector of RGB tuples.
    :param samples: How many samples shall be taken, low amountscolor  are faster.
    :returns: a :class:`MoodbarDescription` with all values set.
    """
    # Extract the separate channels:
    chan_r, chan_g, chan_b = (extract(vector, chan) for chan in range(3))
    hist_r, hist_g, hist_b = histogram(chan_r), histogram(chan_g), histogram(chan_b)

    # Find the most dominant colors, our most important attribute:
    dominant_colors, blackness = find_dominant_colors(vector, samples // 2)

    # Countervariables:
    max_samples, min_samples = [0] * samples, [0] * samples
    last_r, last_g, last_b = None, None, None
    diff_r, diff_g, diff_b = 0, 0, 0

    discrete = discretize(chan_r, chan_g, chan_b, n=int(1000 / samples))
    for idx, (r, g, b) in enumerate(discrete):
        # This should not happen, and is only there for invalid data:
        if idx >= samples:
            break

        # Always take the highest/lowest current value:
        max_samples[idx], min_samples[idx] = max(r, g, b), min(r, g, b)

        if last_r is not None:
            diff_r += abs(r - last_r)
            diff_g += abs(g - last_g)
            diff_b += abs(b - last_b)

        last_r, last_g, last_b = r, g, b

    average_max = int(sum(max_samples) / samples)
    average_min = int(sum(min_samples) / samples)

    # The potentially maximal diff per channel is (samples - 1) * 255,
    # but we stretch the value since most music will only use at max.
    # a third of that.
    max_diff = ((samples - 1) * 255) / 3

    percentize = lambda v: min(100, int(round(v / max_diff * 100)))
    diff_r, diff_g, diff_b = map(percentize, (diff_r, diff_g, diff_b))

    # Built an easy accesable namedtuple:
    return MoodbarDescription((
                MoodbarChannel(hist_r, diff_r),
                MoodbarChannel(hist_g, diff_g),
                MoodbarChannel(hist_b, diff_b),
            ),
            average_max, average_min,
            dict(dominant_colors), blackness
    )

###########################################################################
#                            Actual Providers                             #
###########################################################################


class MoodbarProvider(Provider):
    """Basic Moodbar Provider.

    Takes a vector of RGB Tuples.
    """
    def do_process(self, vector):
        'Subclassed from Provider, will be called for you on the input.'
        return tuple([process_moodbar(vector)])


class MoodbarMoodFileProvider(MoodbarProvider):
    """Moodbar Provider for pre computed mood files.

    Takes a path to a mood file.
    """
    def do_process(self, mood_file_path):
        try:
            vector = read_moodbar_values(mood_file_path)
            return MoodbarProvider.do_process(self, vector)
        except OSError:
            return None


class MoodbarAudioFileProvider(MoodbarMoodFileProvider):
    """Moodbar Provider for audio files.

    Takes a path to an arbitary audio file.
    Will look for audio_file_path + '.mood' before computing it.
    Resulting mood file will be stored in the same path.
    """
    def do_process(self, audio_file_path):
        mood_file_path = audio_file_path + '.mood'
        if not os.path.exists(mood_file_path):
            if compute_moodbar_for_file(audio_file_path, mood_file_path):
                return None
        return MoodbarMoodFileProvider.do_process(self, mood_file_path)


if __name__ == '__main__':
    import sys
    import unittest

    if '--cli' in sys.argv:
        # This expects a mood.file in the current directory
        vector = read_moodbar_values('mood.file')
        print(process_moodbar(vector, samples=10))
    else:
        unittest.main()
