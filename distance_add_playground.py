import igraph
from collections import deque, OrderedDict
from operator import itemgetter

import sys
float_cmp = lambda a, b: abs(a - b) < sys.float_info.epsilon


uids = 0

def cs():
    global uids
    s = Song()
    s._max_neighbors = 3
    s.uid = uids
    uids += 1
    return s





class Song:
    def __init__(self):
        # d = sorteddict(lambda song: (d.get(song, self._last_dist), id(song)))
        # self._dist_dict = ValueSortedDict()
        self._dist_dict = {}
        self._max_neighbors = 10
        self._max_distance = 0.999

    def distance_add(self, other, distance):
        if other is self:
            return False

        sdd, odd = self._dist_dict, other._dist_dict
        if other in sdd:
            if sdd[other] < distance:
                return False  # Reject

            # The key was already in..
            # so we need to delete it to get the sorting right:
            # the key function must return the same key for each item always.
            # So the only way to get out of this is to remove the old item
            # and add a new one.
            del sdd[other]

            # Since we delete the worst song always only in one direction,
            # we gonna need to pay attention here.
            # (we didn't need to secure the top one, since we checked
            # already with the in operator)
            try:
                del odd[self]
            except KeyError:
                pass

        elif distance <= self._max_distance:
            # Check if we still have room left
            if len(sdd) >= self._max_neighbors:
                # Find the worst song in the dictionary
                worst_song, worst_dist = max(sdd.items(), key=itemgetter(1))
                if distance >= worst_dist:
                    return False
                # delete the worst one to make place,
                # BUT: do not delete the connection from worst to self
                # we create unidir edges here on purpose.
                del sdd[worst_song]
        else:
            return False

        # Add the new element:
        sdd[other] = odd[self] = distance
        return True

    def distance_finalize(self):
        to_delete = deque()
        for other in self._dist_dict:
            dist_a, dist_b = self.distance_get(other), other.distance_get(self)
            if dist_a is None:
                to_delete.append((other, self))
            if dist_b is None:
                to_delete.append((self, other))

        for source, target in to_delete:
            del source._dist_dict[target]

        self._dist_dict = OrderedDict(sorted(self._dist_dict.items(), key=itemgetter(1)))

    def distance_get(self, other):
        return self._dist_dict.get(other)

    def __repr__(self):
        return '<#{} {}>'.format(
            self.uid,
            [song.uid for song in self._dist_dict.keys()]
        )

    def __lt__(self, other):
        return id(self) < id(other)

    def distance_iter(self):
        return self._dist_dict.items()


if __name__ == '__main__':
    songs = []
    N = 1000
    for uid in range(N):
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
    for i in range(3):
        for i, window in enumerate(sliding_window(songs, 50,  25)):
            for j, (song_a, song_b) in enumerate(combinations(window, 2)):
                a, b = 1.0 - song_a.uid / N, 1.0 - song_b.uid / N
                dist = abs(a - b)
                # dist = euler (i * j % 30)
                done = Song.distance_add(song_a, song_b, dist)

    for song in songs:
        song.distance_finalize()

    for song in songs:
        last = None
        for other, dist in song.distance_iter():
            if last is not None and last > dist:
                print('!!! unsorted', last, dist)
            last = dist

    g = igraph.Graph(directed=False)
    g.add_vertices(len(songs))

    edge_set = deque()
    for song_a in songs:
        # print(len(song_a._dist_pool))
        for song_b, _ in song_a.distance_iter():
            #print(song_a, '->', song_b)
            # Make Edge Deduplication work:
            if song_a.uid < song_b.uid:
                edge_set.append((song_b.uid, song_a.uid))
            else:
                edge_set.append((song_a.uid, song_b.uid))

    # Filter duplicate edge pairs.
    g.add_edges(set(edge_set))

    # visual_style = {}
    # visual_style['layout'] = g.layout('fr')
    # visual_style['vertex_label'] = [str(vx.index) for vx in g.vs]
    # igraph.plot(g, **visual_style)
