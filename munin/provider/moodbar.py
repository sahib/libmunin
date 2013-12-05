#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
import os

from collections import deque, Counter, namedtuple
from operator import itemgetter

# Fix for Python 3.2
import subprocess
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'w')

# Internal:
from munin.utils import grouper
from munin.provider import Provider

# External:
from igraph.statistics import Histogram


MoodbarDescription = namedtuple('MoodbarDescription', [
        'channels',
        'average_max', 'average_min',
        'dominant_colors', 'blackness'
])


MoodbarDescription.__repr__ = lambda self: '''\
Red:
    Histogram: {hist_r}
    Diffsum:   {diff_r}

Green:
    Histogram: {hist_g}
    Diffsum:   {diff_g}

Blue:
    Histogram: {hist_b}
    Diffsum:   {diff_b}

Average Minimum: {avg_min}
Average Maximum: {avg_max}
Dominant colors:

    {dominant_colors}
'''.format(
    hist_r=self.channels[0].histogram, diff_r=self.channels[0].diffsum,
    hist_g=self.channels[1].histogram, diff_g=self.channels[1].diffsum,
    hist_b=self.channels[2].histogram, diff_b=self.channels[2].diffsum,
    avg_min=self.average_min,
    avg_max=self.average_max,
    dominant_colors='\n    '.join(
        ['({:>3d}, {:>3d}, {:>3d})'.format(r, g, b) for r, g, b in self.dominant_colors]
    )
)


MoodbarChannel = namedtuple('MoodbarChannel', [
    'histogram', 'diffsum'
])


def compute_moodbar_for_file(audio_file, output_file, print_output=False):
    '''Call a moodbar process on a certain audio file.

    :param audio_file: Path to an arbitary audio file.
    :param output_file: Path to where the outputfile shall be written.
    :param print_output: Print the output of the moodbar utility?

    :returns: The exit code of the moodbar utility (0 on success).
    '''
    stdout, stderr = DEVNULL, DEVNULL
    if print_output:
        stdout, stderr = None, None

    return subprocess.call(
            ['moodbar', audio_file, '-o', output_file],
            stdout=stdout, stderr=stderr
    )


def read_moodbar_values(path):
    '''Read a vector of RGB triples from a mood-file (as produced by moodbar).

    :param path: The path where the mood file is located.
    :returns: A list of 1000 RGB Triples.
    '''
    with open(path, 'rb') as f:
        return [tuple(rgb) for rgb in grouper(f.read(), n=3)]


def discretize(chan_r, chan_g, chan_b, n=50):
    '''Split the list down into blocks and calculate their mean.
    Results in a smaller (original_len / n) list with approximated values.

    :param chan_r: Iterable of the red channel
    :param chan_g: Iterable of the green channel
    :param chan_b: Iterable of the blue channel
    :param n: How big the block size shall be.
    :returns: A generator that yields the new list lazily.
    '''
    for gr, gg, gb in zip(*(grouper(c, n) for c in (chan_r, chan_g, chan_b))):
        yield sum(gr) / n, sum(gg) / n, sum(gb) / n


def histogram(channel, bin_width=51):
    '''Calculate a histogram (i.e. a binned counter of elements) of an iterable.

    :param channel: The channel to consider.
    :param bin_width: The width of each bin (255 / bin_width == 0!)
    :returns: a list of binned values (len = 255 / bin_width)
    '''
    hist = Histogram(bin_width=bin_width, data=channel)
    return [value for s, e, value in hist.bins()]


def extract(vector, chan_idx):
    '''Extract a certain channel from an iterable of rgb triples.

    :param vector: The vector with rgb triples.
    :param chan_idx: The idx of the desired channel
    :returns: A flat list with the single values
    '''
    f = itemgetter(chan_idx)
    return [f(rgb) for rgb in vector]


def find_dominant_colors(vector, samples, roundoff=17):
    '''Find the most dominant colors in the vector.

    :param vector: The vector of rgb triples.
    :param samples: How many dominant colors to find.
    :param roundoff: How much grouping shall be done,
                     high numbers lead to less possible colors.

    :returns: A list with the dominant colors (max len is samples)
              and the percent of black colors as integer.
    '''
    blackness_count, result = 0, []
    data = [tuple([int(v / roundoff) * roundoff for v in rgb]) for rgb in vector]

    for color, count in Counter(data).most_common():
        # Do not count very dark colors:
        if all(map(lambda channel: channel <= roundoff, color)):
            blackness_count += count
        else:
            result.append((color, count))

    return result[:samples], int(round(blackness_count / 10))


def process_moodbar(vector, samples=25):
    '''Turn a moodbar vector into a :class:`MoodbarDescription`.

    :param vector: The vector of RGB tuples.
    :param samples: How many samples shall be taken, low amountscolor  are faster.
    :returns: a :class:`MoodbarDescription` with all values set.
    '''
    # Extract the separate channels:
    chan_r, chan_g, chan_b = (extract(vector, chan) for chan in range(3))
    hist_r, hist_g, hist_b = histogram(chan_r), histogram(chan_g), histogram(chan_b)

    # Find the most dominant colors, our most important attribute:
    dominant_colors, blackness = find_dominant_colors(vector, samples)

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

    # The potentially maximal diff per channel:
    max_diff = samples * 255
    diff_r, diff_g, diff_b = (int(round(v / max_diff * 100)) for v in (diff_r, diff_g, diff_b))

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
    '''Basic Moodbar Provider.

    Takes a vector of RGB Tuples.
    '''
    def __init__(self):
        Provider.__init__(self, 'Moodbar', is_reversible=False)

    def process(self, vector):
        'Subclassed from Provider, will be called for you on the input.'
        return tuple([process_moodbar(vector)])

    def reverse(self, output_values):
        raise NotImplemented('moodbars are not reversible')


class MoodbarMoodFileProvider(MoodbarProvider):
    '''Moodbar Provider for pre computed mood files.

    Takes a path to a mood file.
    '''
    def process(self, mood_file_path):
        try:
            vector = read_moodbar_values(mood_file_path)
            return MoodbarProvider.process(self, vector)
        except OSError:
            return ()


class MoodbarAudioFileProvider(MoodbarMoodFileProvider):
    '''Moodbar Provider for audio files.

    Takes a path to an arbitary audio file.
    Will look for audio_file_path + '.mood' before computing it.
    Resulting mood file will be stored in the same path.
    '''
    def process(self, audio_file_path):
        mood_file_path = audio_file_path + '.mood'
        if not os.path.exists(mood_file_path):
            if compute_moodbar_for_file(audio_file_path, mood_file_path) is not 0:
                return ()
        return MoodbarMoodFileProvider.process(self, mood_file_path)


if __name__ == '__main__':
    import sys
    import unittest

    if '--cli' in sys.argv:
        vector = read_moodbar_values('mood.file')
        print(process_moodbar(vector, samples=10))
    else:
        unittest.main()
