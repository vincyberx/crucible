import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from allocate import allocate  # noqa: E402


class TestRemainderRule(unittest.TestCase):
    def test_largest_remainder_not_first_index(self):
        # floors 1,3,5 ; remainders 4,2,0 -> index 0 gets the cent
        self.assertEqual(allocate(10, [1, 2, 3]), [2, 3, 5])

    def test_largest_remainder_last_index(self):
        # 7*[1,1,2]/4 -> 1.75, 1.75, 3.5 ; floors 1,1,3 ; rems 3,3,2 -> idx 0 and 1
        self.assertEqual(allocate(7, [1, 1, 2]), [2, 2, 3])

    def test_remainder_goes_to_middle(self):
        # 10*[2,5,3]/10 exact ; 11*[2,5,3]/10 -> 2.2, 5.5, 3.3 -> idx 1
        self.assertEqual(allocate(11, [2, 5, 3]), [2, 6, 3])

    def test_ties_lower_index_first(self):
        self.assertEqual(allocate(5, [1, 1, 1, 1]), [2, 1, 1, 1])
        self.assertEqual(allocate(2, [1, 1, 1]), [1, 1, 0])
        self.assertEqual(allocate(3, [1, 1, 1, 1]), [1, 1, 1, 0])

    def test_zero_weights_get_nothing(self):
        self.assertEqual(allocate(7, [0, 1, 0, 1]), [0, 4, 0, 3])
        self.assertEqual(allocate(5, [0, 0, 3]), [0, 0, 5])
        self.assertEqual(allocate(1, [0, 1, 1]), [0, 1, 0])


class TestNegative(unittest.TestCase):
    def test_negative_mirrors_positive(self):
        self.assertEqual(allocate(-100, [1, 1, 1]), [-34, -33, -33])

    def test_negative_with_remainder(self):
        self.assertEqual(allocate(-10, [1, 2, 3]), [-2, -3, -5])
        self.assertEqual(allocate(-5, [1, 1, 1, 1]), [-2, -1, -1, -1])

    def test_negative_generic(self):
        rng = random.Random(1234)
        for _ in range(200):
            n = rng.randint(1, 6)
            weights = [rng.randint(0, 9) for _ in range(n)]
            if sum(weights) == 0:
                weights[0] = 1
            total = rng.randint(1, 10_000)
            self.assertEqual(allocate(-total, weights), [-x for x in allocate(total, weights)])


class TestExactness(unittest.TestCase):
    def test_huge_total(self):
        self.assertEqual(allocate(10**20 + 1, [1, 1]), [5 * 10**19 + 1, 5 * 10**19])

    def test_huge_total_three_way(self):
        total = 2**70 + 2
        q, r = divmod(total, 3)
        self.assertEqual(r, 0)
        self.assertEqual(allocate(total, [1, 1, 1]), [q, q, q])
        self.assertEqual(allocate(total + 1, [1, 1, 1]), [q + 1, q, q])

    def test_huge_weights(self):
        w = 10**30
        self.assertEqual(allocate(3, [w, w + 1]), [1, 2])

    def test_properties_random(self):
        rng = random.Random(42)
        for _ in range(300):
            n = rng.randint(1, 8)
            weights = [rng.randint(0, 50) for _ in range(n)]
            if sum(weights) == 0:
                weights[-1] = 3
            total = rng.randint(0, 100_000)
            result = allocate(total, weights)
            self.assertEqual(len(result), n)
            self.assertEqual(sum(result), total)
            w_sum = sum(weights)
            for share, w in zip(result, weights):
                self.assertTrue(all(isinstance(x, int) for x in result))
                floor_q = total * w // w_sum
                self.assertIn(share, (floor_q, floor_q + 1))
                if w == 0:
                    self.assertEqual(share, 0)


class TestValidation(unittest.TestCase):
    def test_empty_weights(self):
        with self.assertRaises(ValueError):
            allocate(10, [])

    def test_all_zero_weights(self):
        with self.assertRaises(ValueError):
            allocate(10, [0, 0])

    def test_negative_weight(self):
        with self.assertRaises(ValueError):
            allocate(10, [1, -1, 2])


if __name__ == "__main__":
    unittest.main()
