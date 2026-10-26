import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from versions import compare, sort_versions  # noqa: E402


class TestPrereleasePrecedence(unittest.TestCase):
    def test_numeric_identifiers_numeric_order(self):
        self.assertEqual(compare("1.0.0-alpha.2", "1.0.0-alpha.10"), -1)
        self.assertEqual(compare("1.0.0-rc.11", "1.0.0-rc.9"), 1)

    def test_numeric_lower_than_alphanumeric(self):
        self.assertEqual(compare("1.0.0-alpha.1", "1.0.0-alpha.beta"), -1)
        self.assertEqual(compare("1.0.0-1", "1.0.0-alpha"), -1)
        self.assertEqual(compare("1.0.0-999", "1.0.0-0a"), -1)

    def test_shorter_prerelease_lower(self):
        self.assertEqual(compare("1.0.0-alpha", "1.0.0-alpha.1"), -1)
        self.assertEqual(compare("1.0.0-alpha.1.2", "1.0.0-alpha.1"), 1)

    def test_ascii_lexical_case_sensitive(self):
        self.assertEqual(compare("1.0.0-Beta", "1.0.0-alpha"), -1)
        self.assertEqual(compare("1.0.0-alpha", "1.0.0-alphA"), 1)

    def test_alphanumeric_lexical_not_numeric(self):
        self.assertEqual(compare("1.0.0-rc10", "1.0.0-rc9"), -1)

    def test_hyphen_inside_prerelease(self):
        self.assertEqual(compare("1.0.0-alpha-2", "1.0.0-alpha-10"), 1)
        self.assertEqual(compare("1.0.0-x-y-z.1", "1.0.0-x-y-z.1"), 0)

    def test_prerelease_of_higher_core_wins(self):
        self.assertEqual(compare("1.0.1-alpha", "1.0.0"), 1)
        self.assertEqual(compare("2.0.0-rc.1", "1.99.99"), 1)

    def test_big_numbers(self):
        self.assertEqual(compare("1.0.0-123456789012345678901", "1.0.0-123456789012345678902"), -1)
        self.assertEqual(compare("10000000000000000000000.0.0", "9999999999999999999999.9.9"), 1)

    def test_full_chain(self):
        chain = [
            "1.0.0-0.3.7",
            "1.0.0-1",
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-alpha.beta",
            "1.0.0-beta",
            "1.0.0-beta.2",
            "1.0.0-beta.11",
            "1.0.0-rc.1",
            "1.0.0",
            "1.0.1-alpha",
        ]
        for lo, hi in zip(chain, chain[1:]):
            self.assertEqual(compare(lo, hi), -1, (lo, hi))
            self.assertEqual(compare(hi, lo), 1, (hi, lo))


class TestBuildMetadata(unittest.TestCase):
    def test_build_ignored(self):
        self.assertEqual(compare("1.0.0+a", "1.0.0+b"), 0)
        self.assertEqual(compare("1.0.0+20260101", "1.0.0"), 0)
        self.assertEqual(compare("1.0.0-rc.1+build.5", "1.0.0-rc.1"), 0)

    def test_build_does_not_raise_prerelease(self):
        self.assertEqual(compare("1.0.0-rc.1+zzz", "1.0.0"), -1)

    def test_build_with_hyphen_and_leading_zero(self):
        self.assertEqual(compare("1.0.0+build-007.01", "1.0.0"), 0)

    def test_hyphen_after_plus_is_build(self):
        self.assertEqual(compare("1.0.0+exp-sha.5114f85", "1.0.0"), 0)


class TestSorting(unittest.TestCase):
    def test_sort_mixed(self):
        data = ["1.0.0", "1.0.0-rc.1", "1.0.0-alpha.10", "1.0.0-alpha.2", "0.9.0", "1.0.0-alpha"]
        self.assertEqual(
            sort_versions(data),
            ["0.9.0", "1.0.0-alpha", "1.0.0-alpha.2", "1.0.0-alpha.10", "1.0.0-rc.1", "1.0.0"],
        )

    def test_sort_is_stable_for_equal_precedence(self):
        data = ["1.0.0+b", "0.1.0", "1.0.0+a", "1.0.0"]
        self.assertEqual(sort_versions(data), ["0.1.0", "1.0.0+b", "1.0.0+a", "1.0.0"])

    def test_sort_returns_new_list(self):
        data = ["2.0.0", "1.0.0"]
        result = sort_versions(data)
        self.assertEqual(result, ["1.0.0", "2.0.0"])
        self.assertEqual(data, ["2.0.0", "1.0.0"])

    def test_sort_rejects_invalid(self):
        with self.assertRaises(ValueError):
            sort_versions(["1.0.0", "1.0"])


class TestValidation(unittest.TestCase):
    INVALID = [
        "1.2",
        "1.2.3.4",
        "01.2.3",
        "1.02.3",
        "1.2.03",
        "v1.2.3",
        " 1.2.3",
        "1.2.3 ",
        "1.2.3-",
        "1.2.3+",
        "1.2.3-alpha..1",
        "1.2.3-alpha.",
        "1.2.3-.alpha",
        "1.2.3-01",
        "1.2.3-alpha.007",
        "1.2.3-al_pha",
        "1.2.3+bu_ild",
        "1.2.3+build..1",
        "1.2.3+a+b",
        "a.b.c",
        "1.2.-3",
        "",
    ]

    VALID = [
        "0.0.0",
        "1.2.3-0",
        "1.2.3-0a",
        "1.2.3-00a",
        "1.2.3--",
        "1.2.3-a-b-c",
        "1.2.3+001",
        "1.2.3-rc.1+build.01",
    ]

    def test_invalid_versions_raise(self):
        for v in self.INVALID:
            with self.subTest(v=v):
                with self.assertRaises(ValueError):
                    compare(v, "1.0.0")
                with self.assertRaises(ValueError):
                    compare("1.0.0", v)

    def test_valid_versions_accepted(self):
        for v in self.VALID:
            with self.subTest(v=v):
                self.assertIn(compare(v, v), (0,))


if __name__ == "__main__":
    unittest.main()
