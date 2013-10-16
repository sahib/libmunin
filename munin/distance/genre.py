#!/usr/bin/env python
# encoding: utf-8


from munin.distance import Distance


'''

    >>> a
    [(85, 0), (190, 2), (190, 6)]
    >>> b
    [(85, 0), (190, 2, 0), (190, 2, 1), (190, 6)]
    >>>


'''


def compare_single_path(left, right):
    n = 0.0
    for l, r in zip(left, right):
        if l == r:
            n += 1
        else:
            break

    return 1 - n / (max(len(left), len(right)) or 1)


class GenreDistance(Distance):
    def _calculate_distance(self, lefts, rights):
        # sa, sb = set(lefts), set(rights)
        # sect = sa & sb
        # diff = (sa | sb) - sect
        # print(sa, sb, sect, diff, sep='\n')

        dists = 0.0
        tries = 0.0
        # for a in lefts:
        #     for b in lefts:
        #         dists += compare_single_path(a, b)
        #         tries += 1
        for a, b in zip(lefts, rights):
            dists += compare_single_path(a, b)
            tries += 1

        return (dists / tries) if tries is not 0 else 1.0

    def calculate_distance(self, lefts, rights):
        lefts = sorted(lefts)
        rights = sorted(rights)

        dists, tries, r_idx = 0.0, 0, 0

        for left in lefts:
            # Optimization: Since the pathlist is sorted we can pop items that
            # are smaller anyway (yielding a distance of 0)
            first_index = left[0]
            while left > rights[r_idx]:
                # One might argue that we could increment tries here:
                r_idx += 1

            print(rights[r_idx:])

            # If there's nothing left to compare we can break just fine.
            if r_idx >= len(rights):
                break

            # Actually compare the selected paths.
            for candidate in rights[r_idx:]:
                print('     ', left, candidate)

                if first_index == candidate[0]:
                    print('      ###', compare_single_path(left, candidate))
                    dists += compare_single_path(left, candidate)
                    tries += 1
                else:
                    print('     ', 'break')
                    break

        print('Tries', tries)
        print('Dists', dists)
        return (dists / tries) if tries is not 0 else 1.0


if __name__ == '__main__':
    import unittest

    float_cmp = lambda a, b: abs(a - b) < 0.00000000001

    class TestSinglePathCompare(unittest.TestCase):
        def test_valid(self):
            inputs = [
                ((190, 1, 0), (190, 1, 0), 0),
                ((190, 1, 0), (190, 1, 1), 1 / 3),
                ((190, 0, 1), (190, 1, 0), 2 / 3),
                ((190, 0, 1), (191, 1, 0),  1),
                ((190, 0, 1), (190, 0, 1, 0), 1 / 4),
                ((190, ), (), 1),
                ((), (), 1)
            ]

            for left, right, result in inputs:
                self.assertTrue(
                        float_cmp(compare_single_path(left, right), result)
                        and
                        float_cmp(compare_single_path(right, left), result)
                )

    class TestGenreDistance(unittest.TestCase):
        def test_valid(self):
            calc = GenreDistance()
            a = [(85, 0), (190, 2), (190, 6)]
            b = [(85, 0), (190, 2, 0), (190, 2, 1), (190, 6)]
            print('   =', calc.calculate_distance(a, b))
            print('   =', calc.calculate_distance(b, a))
            print('   =', calc.calculate_distance(a, a))
            print('   =', calc.calculate_distance(b, b))

        def test_invalid(self):
            'Test rather unusual corner cases'
            pass

    unittest.main()
