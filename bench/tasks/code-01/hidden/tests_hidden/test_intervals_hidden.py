import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intervals import union  # noqa: E402


class TestTouching(unittest.TestCase):
    def test_open_open_touch_stays_separate(self):
        self.assertEqual(union(["[1,5)", "(5,7]"]), ["[1,5)", "(5,7]"])

    def test_open_intervals_touch_stays_separate(self):
        self.assertEqual(union(["(1,5)", "(5,9)"]), ["(1,5)", "(5,9)"])

    def test_half_open_touch_merges_left_open(self):
        self.assertEqual(union(["[1,5)", "[5,7]"]), ["[1,7]"])

    def test_half_open_touch_merges_right_open(self):
        self.assertEqual(union(["[1,5]", "(5,7]"]), ["[1,7]"])

    def test_point_fills_gap(self):
        self.assertEqual(union(["[1,5)", "[5,5]", "(5,7]"]), ["[1,7]"])

    def test_point_fills_gap_any_order(self):
        self.assertEqual(union(["(5,7]", "[5,5]", "[1,5)"]), ["[1,7]"])

    def test_real_line_not_integers(self):
        self.assertEqual(union(["[1,2]", "[3,4]"]), ["[1,2]", "[3,4]"])

    def test_chain(self):
        self.assertEqual(union(["[0,1)", "[1,2)", "[2,3)", "(3,4]"]), ["[0,3)", "(3,4]"])


class TestDegenerate(unittest.TestCase):
    def test_empty_degenerates_vanish(self):
        self.assertEqual(union(["[3,3)", "(3,3]", "(3,3)"]), [])

    def test_closed_point_kept(self):
        self.assertEqual(union(["[3,3]"]), ["[3,3]"])

    def test_empty_degenerate_does_not_fill_gap(self):
        self.assertEqual(union(["[1,5)", "[5,5)", "(5,7]"]), ["[1,5)", "(5,7]"])

    def test_point_inside(self):
        self.assertEqual(union(["[1,5]", "[3,3]"]), ["[1,5]"])

    def test_point_closes_open_right_end(self):
        self.assertEqual(union(["(1,5)", "[5,5]"]), ["(1,5]"])

    def test_point_closes_open_left_end(self):
        self.assertEqual(union(["[1,1]", "(1,4)"]), ["[1,4)"])

    def test_separate_points(self):
        self.assertEqual(union(["[2,2]", "[1,1]", "[2,2]"]), ["[1,1]", "[2,2]"])


class TestInclusiveness(unittest.TestCase):
    def test_same_end_closed_wins(self):
        self.assertEqual(union(["[1,5)", "[2,5]"]), ["[1,5]"])

    def test_same_end_closed_first(self):
        self.assertEqual(union(["[1,5]", "[2,5)"]), ["[1,5]"])

    def test_same_start_closed_wins(self):
        self.assertEqual(union(["(1,3]", "[1,2]"]), ["[1,3]"])

    def test_same_start_and_end_closed_wins(self):
        self.assertEqual(union(["(1,3]", "[1,3]"]), ["[1,3]"])

    def test_same_start_open_then_closed_shorter(self):
        self.assertEqual(union(["(1,3)", "[1,2)"]), ["[1,3)"])

    def test_same_start_both_open(self):
        self.assertEqual(union(["(1,3]", "(1,2]"]), ["(1,3]"])

    def test_same_start_open_longer(self):
        self.assertEqual(union(["(1,2]", "[1,1]"]), ["[1,2]"])

    def test_identical_open(self):
        self.assertEqual(union(["(0,1)", "(0,1)"]), ["(0,1)"])


class TestParsing(unittest.TestCase):
    def test_whitespace_and_negative(self):
        self.assertEqual(union(["[ -3 , 4 )", "[4, 6]"]), ["[-3,6]"])

    def test_negative_open(self):
        self.assertEqual(union(["(-10,-5)", "(-5,0]"]), ["(-10,-5)", "(-5,0]"])

    def test_start_greater_than_end(self):
        with self.assertRaises(ValueError):
            union(["[5,1]"])

    def test_missing_bracket(self):
        with self.assertRaises(ValueError):
            union(["[1,2"])

    def test_wrong_brackets(self):
        with self.assertRaises(ValueError):
            union(["{1,2}"])

    def test_non_integer(self):
        with self.assertRaises(ValueError):
            union(["[1.5,2]"])

    def test_error_even_when_other_items_valid(self):
        with self.assertRaises(ValueError):
            union(["[1,2]", "[3,x]"])


if __name__ == "__main__":
    unittest.main()
