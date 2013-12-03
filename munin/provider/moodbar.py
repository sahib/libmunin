#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from collections import deque, Counter
from operator import itemgetter

# Internal:
from munin.utils import grouper
from munin.provider import Provider

# External:
from igraph.statistics import Histogram


def read_moodbar_values(path):
    with open(path, 'rb') as f:
        return [tuple(rgb) for rgb in grouper(f.read(), n=3)]


def discretize(chan_r, chan_g, chan_b, n=50):
    for gr, gg, gb in zip(grouper(chan_r, n), grouper(chan_g, n), grouper(chan_b, n)):
        yield sum(gr) / n, sum(gg) / n, sum(gb) / n


def histogram(channel, bin_width=17, take_max=5):
    hist = Histogram(bin_width=bin_width, data=channel)
    hist_data = [(int((s + e) / 2), value) for s, e, value in hist.bins()][:take_max]
    return hist_data, int(round(hist.mean)), int(round(hist.sd))


def extract(vector, chan):
    f = itemgetter(chan)
    return [f(rgb) for rgb in vector]


def find_dominant_colors(vector, samples, roundoff=15):
    data = [tuple([int(v / roundoff) * roundoff for v in rgb]) for rgb in vector]
    counter = list(Counter(data).most_common(samples * 2))

    blackness_count, result = 0, []
    for color, count in counter:
        # Do not count very dark colors:
        if all(map(lambda v: v < 20, color)):
            blackness_count += count
        else:
            result.append((color, count))

    return result[:samples], int(round(blackness_count / 10))


def process_moodbar(vector, samples=20, print_to_sdout=False):
    chan_r, chan_g, chan_b = (extract(vector, chan) for chan in range(3))
    hist_r, mean_r, sd_r = histogram(chan_r)
    hist_g, mean_g, sd_g = histogram(chan_g)
    hist_b, mean_b, sd_b = histogram(chan_b)

    # dominant_colors = Counter(vector).most_common(samples)
    dominant_colors, blackness = find_dominant_colors(vector, samples)
    max_samples, min_samples = [0] * samples, [0] * samples

    last_r, last_g, last_b = None, None, None
    diff_r, diff_g, diff_b = 0, 0, 0

    for idx, (r, g, b) in enumerate(discretize(chan_r, chan_g, chan_b, n=int(1000 / samples))):
        if idx >= samples:
            break

        max_samples[idx], min_samples[idx] = max(r, g, b), min(r, g, b)

        if last_r is not None:
            diff_r += abs(r - last_r)
            diff_g += abs(r - last_g)
            diff_b += abs(r - last_b)

        last_r, last_g, last_b = r, g, b

    average_max = int(sum(max_samples) / samples)
    average_min = int(sum(min_samples) / samples)

    # The potentially maximal diff per channel:
    max_diff = samples * 255
    diff_r, diff_g, diff_b = (int(round(v / max_diff * 100)) for v in (diff_r, diff_g, diff_b))

    if print_to_sdout:
        def print_channel(hist, mean, sd, diff):
            print('    hist:', ', '.join(('{:d} ({:d}x)'.format(value, count) for value, count in hist)))
            print('    mean:', mean)
            print('    sdev:', sd)
            print('    diff:', diff)

        print('channel red:')
        print_channel(hist_r, mean_r, sd_r, diff_r)
        print('channel green:')
        print_channel(hist_g, mean_g, sd_g, diff_g)
        print('channel blue:')
        print_channel(hist_b, mean_b, sd_b, diff_b)
        print()
        print('average maximum:')
        print('    ', average_max)
        print('average minimum:')
        print('    ', average_min)
        print()
        print('dominant colors ({:d}% black):'.format(blackness))
        for color, count in dominant_colors:
            color_string = '({:>3d}, {:>3d}, {:>3d})'.format(*color)
            print('    {: 4d}x: {}'.format(count, color_string))

    return hist_r, hist_g, hist_b, \
           mean_r, mean_g, mean_b, \
           sd_r, sd_g, sd_b, \
           diff_r, diff_g, diff_b, \
           average_max, average_min, \
           dominant_colors, blackness


class MoodbarProvider(Provider):
    def __init__(self):
        Provider.__init__(self, 'Moodbar', is_reversible=False)

    def process(self, input_value):
        'Subclassed from Provider, will be called for you on the input.'
        try:
            vector = read_moodbar_values(input_value)
            return tuple([process_moodbar(vector)])
        except OSError:
            return ()

    def reverse(self, output_values):
        raise NotImplemented('Moodbars are not reversible')


if __name__ == '__main__':
    import sys
    import unittest

    if '--cli' in sys.argv:
        vector = read_moodbar_values('mood.file')
        process_moodbar(vector, samples=10, print_to_sdout=True)
    else:
        unittest.main()
