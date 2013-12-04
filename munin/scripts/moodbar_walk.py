#!/usr/bin/env python
# encoding: utf-8


import os
import sys

from itertools import combinations
from collections import deque


from munin.provider.moodbar import MoodbarAudioFileProvider
from munin.distance.moodbar import MoodbarDistance


if __name__ == '__main__':
    provider = MoodbarAudioFileProvider()
    distance = MoodbarDistance(provider)
    moodbar_descr = deque()

    for root, directory, paths in os.walk(sys.argv[1]):
        print(root)
        for path in paths:
            if path.endswith('.mood'):
                continue

            print('    ', path)
            os.chdir(root)
            full_path = os.path.join(root, path)
            result = provider.process(full_path)
            if result:
                moodbar_descr.append((result, path, root))

    moodbar_descr = list(moodbar_descr)
    pairs = deque()

    for idx_a, idx_b in combinations(range(len(moodbar_descr)), 2):
        descr_a, path_a, root_a = moodbar_descr[idx_a]
        descr_b, path_b, root_b = moodbar_descr[idx_b]
        pairs.append((distance.compute(descr_a, descr_b), path_a, path_b, root_a, root_b))

    for final_distance, path_a, path_b, root_a, root_b in sorted(pairs, key=lambda e: e[0]):
        same = 'Y' if root_a == root_b else 'N'
        print('[{}] {:.5f}: {:>50s} -> {:<50s}'.format(same, final_distance, path_a, path_b))
