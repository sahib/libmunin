#!/usr/bin/env python
# encoding: utf-8


import os
import sys

from itertools import combinations
from collections import deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Queue


from munin.provider.moodbar import MoodbarAudioFileProvider
from munin.distance.moodbar import MoodbarDistance


def compute_moodbar(path_root):
    try:
        path, root = path_root
        full_path = os.path.join(root, path)
        result = provider.process(full_path)
        if result:
            return (result, path, root)
    except Exception as e:
        pass

    return (None, path, root)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: {} path_to_music_dir'.format(sys.argv[0]))
        sys.exit(-1)

    provider = MoodbarAudioFileProvider()
    distance = MoodbarDistance(provider)
    moodbar_files = deque()

    for root, directory, paths in os.walk(sys.argv[1]):
        print(root)
        for path in paths:
            if path.endswith('.mood'):
                continue

            print('    ', path)
            moodbar_files.append((path, root))

    moodbar_descr = []
    with ProcessPoolExecutor(max_workers=10) as executor:
        futured = executor.map(compute_moodbar, moodbar_files)
        for descr, path, root in futured:
            if descr is not None:
                moodbar_descr.append((descr, path, root))

    pairs = deque()
    for idx_a, idx_b in combinations(range(len(moodbar_descr)), 2):
        descr_a, path_a, root_a = moodbar_descr[idx_a]
        descr_b, path_b, root_b = moodbar_descr[idx_b]
        pairs.append((
            distance.compute(descr_a, descr_b),
            path_a, path_b, root_a, root_b
        ))

    sorted_pairs = sorted(pairs, key=lambda e: e[0])
    for final_distance, path_a, path_b, root_a, root_b in sorted_pairs:
        same = 'Y' if root_a == root_b else 'N'
        print('[{}] {:.5f}: {:>50s} -> {:<50s}'.format(
            same, final_distance, path_a, path_b
        ))
