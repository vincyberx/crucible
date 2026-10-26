import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from template import render  # noqa: E402


class TestRenderBasics(unittest.TestCase):
    def test_plain_text(self):
        self.assertEqual(render("hello world", {}), "hello world")

    def test_simple_substitution(self):
        self.assertEqual(render("Hi {name}!", {"name": "Ada"}), "Hi Ada!")

    def test_multiple_and_numbers(self):
        self.assertEqual(render("{a}+{b}", {"a": 1, "b": 2}), "1+2")

    def test_nested_path(self):
        ctx = {"user": {"name": "Ada"}}
        self.assertEqual(render("Hi {user.name}", ctx), "Hi Ada")

    def test_default_when_missing(self):
        self.assertEqual(render("{city|n/a}", {}), "n/a")

    def test_escaped_braces(self):
        self.assertEqual(render("{{literal}}", {}), "{literal}")


if __name__ == "__main__":
    unittest.main()
