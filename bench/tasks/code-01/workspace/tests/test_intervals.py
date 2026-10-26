import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intervals import union  # noqa: E402


class TestUnionBasics(unittest.TestCase):
    def test_overlapping_closed(self):
        self.assertEqual(union(["[1,3]", "[2,5]"]), ["[1,5]"])

    def test_disjoint_closed(self):
        self.assertEqual(union(["[1,2]", "[4,6]"]), ["[1,2]", "[4,6]"])

    def test_output_is_sorted(self):
        self.assertEqual(union(["[5,8]", "[1,3]"]), ["[1,3]", "[5,8]"])

    def test_contained(self):
        self.assertEqual(union(["[1,10]", "[2,3]"]), ["[1,10]"])

    def test_empty_input(self):
        self.assertEqual(union([]), [])


if __name__ == "__main__":
    unittest.main()
