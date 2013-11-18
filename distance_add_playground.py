from blist import sortedset


float_cmp = lambda a, b: abs(a - b) < sys.float_info.epsilon


class Song:
    def __init__(self):
        self._max_neighbors = 5
        self._dist_dict = {}
        self._dist_pool = sortedset(key=lambda e: self._dist_dict[e])

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

        if pop_other is True:
            worst = odp.pop()
            # if worst is not self:
                # print('worst dist other', worst._dist_dict.get(other))
            try:
                del worst._dist_dict[other]
                worst._dist_pool.remove(other)
            except KeyError:
                pass

        if pop_self is True:
            worst = sdp.pop()
            # if worst is not other:
            try:
                del worst._dist_dict[self]
                worst._dist_pool.remove(self)
            except KeyError:
                pass

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
