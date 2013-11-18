from blist import sortedlist


float_cmp = lambda a, b: abs(a - b) < sys.float_info.epsilon


def _remove_link(song, worst):
    print('deleting song', song, id(song), 'from', worst._dist_pool, worst)
    for a in worst._dist_pool:
        print('SONG ID', a.uid, id(a))
        if song is a:
            print('yep found')
        print(a in worst._dist_pool)
        print(worst._dist_pool)
        print(' bisect', worst._dist_pool.bisect(a), len(worst._dist_pool))
    # worst._dist_pool.remove(song)
    del worst._dist_pool[worst._dist_pool.bisect(song)]
    print('deelte done')

    del song._dist_dict[worst]
    del worst._dist_dict[song]


class Song:
    def __init__(self):
        self._max_neighbors = 5
        self._dist_dict = {}
        self._dist_pool = sortedlist(key=lambda e: self._dist_dict[e])

    def distance_add(self, other, distance):
        if self is other:
            return False

        sdd, odd = self._dist_dict, other._dist_dict
        old_dist = sdd.get(other)
        if old_dist is not None and old_dist < distance:
            return False

        sdd[other] = odd[self] = distance
        if old_dist is not None:
            return True

        n, pop_self, pop_other = self._max_neighbors, False, False
        sdp, odp = self._dist_pool, other._dist_pool
        if len(odp) is n:
            if odd[odp[-1]] < distance:
                return False
            pop_other = True

        if len(sdp) is n:
            if sdd[sdp[-1]] < distance:
                return False
            pop_self = True

        print(self, other, distance)
        print(sdp, odp)

        if pop_other is True:
            worst = odp.pop()
            print('worst odp', worst)
            _remove_link(other, worst)

        if pop_self is True:
            worst = sdp.pop()
            print('worst sdp', worst, worst._dist_pool)
            _remove_link(self, worst)

        print(len(sdd), len(odd))

        sdp.add(other)
        odp.add(self)
        return True

    def __repr__(self):
        return '<#{} {}>'.format(
            self.uid,
            [song.uid for song in self._dist_pool]
        )

    def distance_iter(self):
        for entry in self._dist_pool:
            yield entry.song, entry.distance


if __name__ == '__main__':
    songs = []
    for uid in range(100):
        song = Song()
        song.uid = uid
        songs.append(song)

    from itertools import chain, islice, combinations
    import math

    def sliding_window(iterable, n=2, step=1):
        n2 = n // 2
        for idx in range(0, len(iterable), step):
            fst, snd = idx - n2, idx + n2
            if fst < 0:
                yield chain(iterable[fst:], iterable[:snd])
            else:
                yield islice(iterable, fst, snd)

    euler = lambda x: math.fmod(math.e ** x, 1.0)
    for iteration in range(10):
        for i, window in enumerate(sliding_window(songs, 10, 5)):
            for j, (song_a, song_b) in enumerate(combinations(window, 2)):
                Song.distance_add(song_a, song_b, euler(i * j % 30))

    # for song in songs:
    #    print(song)
