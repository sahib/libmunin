from blist import sorteddict


class Song:
    def __init__(self):
        d = sorteddict(lambda e: d.get(e, self._last_dist))
        self._dist_dict = d

    def distance_add(self, other, distance):
        if self is other:
            return False

        self_pool, other_pool = self._dist_dict, other._dist_dict
        if other in self_pool:
            if self_pool[other] < distance:
                return False  # Reject

            # The key was already in.. so we need to delete it to get the
            # sorting thing right.
            del self_pool[other]
            del other_pool[self]

            # Now insert it again.
            self._last_dist = other._last_dist = distance
            self_pool[other] = other_pool[self] = distance
            return True

        pop_self, pop_other = False, False
        if len(self_pool) is 5:
            if self_pool[self_pool.keys()[-1]] < distance:
                return False
            pop_self = True

        if len(other_pool) is 5:
            if other_pool[other_pool.keys()[-1]] < distance:
                return False
            pop_other = True

        if pop_self:
            worst, _ = self_pool.popitem()
            del worst._dist_dict[self]

            # TODO: overtthink this portion
            if len(worst._dist_dict) is 0:
                other._last_dist = worst._last_dist = distance
                other_pool[worst] = worst._dist_dict[other] = distance

        if pop_other:
            worst, _ = other_pool.popitem()
            del worst._dist_dict[other]

            # TODO: overtthink this portion
            if len(worst._dist_dict) is 0:
                self._last_dist = worst._last_dist = distance
                self_pool[worst] = worst._dist_dict[self] = distance

        # add a new entry:
        self._last_dist = other._last_dist = distance
        self_pool[other] = other_pool[self] = distance
        return True

    def __repr__(self):
        return '<#{} {}>'.format(
            self.uid,
            [song.uid for song in self._dist_dict.keys()]
        )

    def distance_iter(self):
        for entry in self._dist_pool:
            yield entry.song, entry.distance


if __name__ == '__main__':
    songs = []
    for uid in range(20):
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
        idx = 0
        for i, window in enumerate(sliding_window(songs, 10, 5)):
            for j, (song_a, song_b) in enumerate(combinations(window, 2)):
                dist = euler(i * j % 30)
                if song_a.uid is 0 or song_b is 0:
                    print('0', song_a, song_b, dist)
                Song.distance_add(song_a, song_b, dist)

    for song in songs:
        print(song)
