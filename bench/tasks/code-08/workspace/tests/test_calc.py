import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calc import EvalError, evaluate  # noqa: E402


class TestEvaluateBasics(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(evaluate("1 + 2 * 3"), 7)
        self.assertEqual(evaluate("(1 + 2) * 3"), 9)

    def test_left_associative_minus(self):
        self.assertEqual(evaluate("10 - 4 - 3"), 3)

    def test_power(self):
        self.assertEqual(evaluate("2 ^ 10"), 1024)

    def test_division_and_remainder(self):
        self.assertEqual(evaluate("7 / 2"), 3)
        self.assertEqual(evaluate("7 % 3"), 1)

    def test_leading_unary_minus(self):
        self.assertEqual(evaluate("-3 + 5"), 2)

    def test_whitespace(self):
        self.assertEqual(evaluate("\t12*(3+4) "), 84)

    def test_syntax_errors(self):
        for bad in ["", "2 +", "(1", "2 $ 3"]:
            with self.assertRaises(EvalError, msg=repr(bad)):
                evaluate(bad)


if __name__ == "__main__":
    unittest.main()
