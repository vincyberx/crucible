import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from allocate import allocate  # noqa: E402


class TestAllocateBasics(unittest.TestCase):
    def test_even_split(self):
        self.assertEqual(allocate(100, [1, 1]), [50, 50])

    def test_exact_proportions(self):
        self.assertEqual(allocate(100, [1, 2, 1]), [25, 50, 25])

    def test_three_way_split(self):
        self.assertEqual(allocate(100, [1, 1, 1]), [34, 33, 33])

    def test_zero_total(self):
        self.assertEqual(allocate(0, [1, 2]), [0, 0])

    def test_sum_is_preserved(self):
        result = allocate(1000, [3, 7, 11])
        self.assertEqual(sum(result), 1000)


if __name__ == "__main__":
    unittest.main()
