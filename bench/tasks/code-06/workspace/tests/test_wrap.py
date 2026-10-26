import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrap import wrap  # noqa: E402


class TestWrapBasics(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(wrap("", 10), [])
        self.assertEqual(wrap("   \n\t ", 10), [])

    def test_fits_on_one_line(self):
        self.assertEqual(wrap("  hello\n\tworld  ", 20), ["hello world"])

    def test_simple_paragraph(self):
        self.assertEqual(
            wrap("the quick brown fox jumps over the lazy dog", 10),
            ["the quick", "brown fox", "jumps over", "the lazy", "dog"],
        )

    def test_exact_fit(self):
        self.assertEqual(wrap("a b c d e f g h", 3), ["a b", "c d", "e f", "g h"])

    def test_long_word_sits_alone(self):
        self.assertEqual(
            wrap("supercalifragilistic is long", 8),
            ["supercalifragilistic", "is long"],
        )

    def test_invalid_width(self):
        with self.assertRaises(ValueError):
            wrap("a b", 0)


if __name__ == "__main__":
    unittest.main()
