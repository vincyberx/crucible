import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from template import render  # noqa: E402


class TestFalsyValues(unittest.TestCase):
    def test_zero_not_replaced_by_default(self):
        self.assertEqual(render("{n|5}", {"n": 0}), "0")

    def test_empty_string_not_replaced(self):
        self.assertEqual(render("[{s|x}]", {"s": ""}), "[]")

    def test_none_renders_as_none(self):
        self.assertEqual(render("{v|x}", {"v": None}), "None")
        self.assertEqual(render("{v}", {"v": None}), "None")

    def test_false_renders(self):
        self.assertEqual(render("{f|yes}", {"f": False}), "False")

    def test_nested_zero(self):
        ctx = {"user": {"name": "Ada", "age": 0}, "n": 3}
        self.assertEqual(render("{user.age|unknown}", ctx), "0")

    def test_non_string_values(self):
        self.assertEqual(render("{xs}", {"xs": [1, 2]}), "[1, 2]")


class TestDefaults(unittest.TestCase):
    def test_default_with_pipes(self):
        self.assertEqual(render("{a|x|y}", {}), "x|y")

    def test_empty_default(self):
        self.assertEqual(render("[{a|}]", {}), "[]")

    def test_default_with_spaces_and_punctuation(self):
        self.assertEqual(render("{a|not set, sorry.}", {}), "not set, sorry.")

    def test_intermediate_not_dict_is_missing(self):
        self.assertEqual(render("{a.b|d}", {"a": "str"}), "d")
        self.assertEqual(render("{a.b|d}", {"a": None}), "d")
        self.assertEqual(render("{a.b.c|d}", {"a": {"b": 5}}), "d")

    def test_list_is_not_indexed(self):
        self.assertEqual(render("{items.0|none}", {"items": ["x"]}), "none")

    def test_digit_key_in_dict(self):
        self.assertEqual(render("{items.0}", {"items": {"0": "zero"}}), "zero")


class TestMissing(unittest.TestCase):
    def test_missing_without_default_raises_keyerror(self):
        with self.assertRaises(KeyError) as cm:
            render("Hi {user.name}", {"user": {}})
        self.assertEqual(cm.exception.args, ("user.name",))

    def test_missing_top_level(self):
        with self.assertRaises(KeyError) as cm:
            render("{x}", {})
        self.assertEqual(cm.exception.args, ("x",))

    def test_intermediate_not_dict_without_default(self):
        with self.assertRaises(KeyError):
            render("{a.b}", {"a": "str"})


class TestEscapes(unittest.TestCase):
    def test_escaped_around_placeholder(self):
        self.assertEqual(render("{{{a}}}", {"a": 1}), "{1}")

    def test_value_then_close_escape(self):
        self.assertEqual(render("{a}}}", {"a": 1}), "1}")

    def test_open_escape_then_value(self):
        self.assertEqual(render("{{{a}", {"a": 1}), "{1")

    def test_escapes_only(self):
        self.assertEqual(render("}}{{", {}), "}{")

    def test_example_table(self):
        ctx = {"user": {"name": "Ada", "age": 0}, "n": 3}
        self.assertEqual(render("{{literal}} {n}", ctx), "{literal} 3")
        self.assertEqual(render("{user.city|n/a}", ctx), "n/a")


class TestSyntaxErrors(unittest.TestCase):
    def assertSyntaxError(self, template):
        with self.assertRaises(ValueError):
            render(template, {"a": 1, "b": {"c": 2}})

    def test_unclosed(self):
        self.assertSyntaxError("x {a")

    def test_stray_close(self):
        self.assertSyntaxError("a } b")

    def test_odd_closing_run(self):
        self.assertSyntaxError("}}}")

    def test_empty_placeholder(self):
        self.assertSyntaxError("{}")

    def test_empty_path_with_default(self):
        self.assertSyntaxError("{|x}")

    def test_double_dot(self):
        self.assertSyntaxError("{a..b}")

    def test_leading_dot(self):
        self.assertSyntaxError("{.a}")

    def test_trailing_dot(self):
        self.assertSyntaxError("{a.}")

    def test_space_in_path(self):
        self.assertSyntaxError("{a b}")
        self.assertSyntaxError("{ a}")

    def test_brace_inside_placeholder(self):
        self.assertSyntaxError("{a|{b}}")

    def test_invalid_char(self):
        self.assertSyntaxError("{a-b}")


if __name__ == "__main__":
    unittest.main()
