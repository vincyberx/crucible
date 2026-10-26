import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from versions import compare, sort_versions  # noqa: E402


class TestVersionBasics(unittest.TestCase):
    def test_numeric_not_lexical(self):
        self.assertEqual(compare("1.2.3", "1.2.10"), -1)

    def test_major_wins(self):
        self.assertEqual(compare("2.0.0", "1.9.9"), 1)

    def test_equal(self):
        self.assertEqual(compare("1.4.2", "1.4.2"), 0)

    def test_prerelease_lower_than_release(self):
        self.assertEqual(compare("1.0.0-alpha", "1.0.0"), -1)

    def test_sort_plain(self):
        self.assertEqual(
            sort_versions(["1.10.0", "1.2.0", "0.9.12", "1.2.1"]),
            ["0.9.12", "1.2.0", "1.2.1", "1.10.0"],
        )


if __name__ == "__main__":
    unittest.main()
