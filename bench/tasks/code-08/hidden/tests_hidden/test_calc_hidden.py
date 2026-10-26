import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calc import EvalError, evaluate  # noqa: E402


class TestPrecedenceAndAssociativity(unittest.TestCase):
    def test_power_is_right_associative(self):
        self.assertEqual(evaluate("2^3^2"), 512)
        self.assertEqual(evaluate("2 ^ 2 ^ 3"), 256)
        self.assertEqual(evaluate("(2^3)^2"), 64)
        self.assertEqual(evaluate("4^3^0"), 4)

    def test_unary_minus_binds_less_tightly_than_power(self):
        self.assertEqual(evaluate("-2^2"), -4)
        self.assertEqual(evaluate("- 2 ^ 2"), -4)
        self.assertEqual(evaluate("(-2)^2"), 4)
        self.assertEqual(evaluate("2 * -2^2"), -8)
        self.assertEqual(evaluate("-3^2 * 2"), -18)
        self.assertEqual(evaluate("1 - -2^2"), 5)

    def test_unary_minus_after_binary_operators(self):
        self.assertEqual(evaluate("2*-3"), -6)
        self.assertEqual(evaluate("2--3"), 5)
        self.assertEqual(evaluate("--3"), 3)
        self.assertEqual(evaluate("-(-3)"), 3)
        self.assertEqual(evaluate("2^--2"), 4)
        self.assertEqual(evaluate("2^-(-3)"), 8)
        self.assertEqual(evaluate("8 / -2 * 3"), -12)


class TestIntegerArithmetic(unittest.TestCase):
    def test_division_truncates_toward_zero(self):
        self.assertEqual(evaluate("-7 / 2"), -3)
        self.assertEqual(evaluate("7 / -2"), -3)
        self.assertEqual(evaluate("-7 / -2"), 3)
        self.assertEqual(evaluate("-1 / 2"), 0)
        self.assertEqual(evaluate("1 / -2"), 0)

    def test_remainder_has_sign_of_dividend(self):
        self.assertEqual(evaluate("-7 % 2"), -1)
        self.assertEqual(evaluate("7 % -2"), 1)
        self.assertEqual(evaluate("-7 % -2"), -1)
        self.assertEqual(evaluate("-6 % 3"), 0)

    def test_big_integers_are_exact(self):
        self.assertEqual(evaluate("2^100"), 1267650600228229401496703205376)
        self.assertEqual(evaluate("10^20 / 3"), 33333333333333333333)
        self.assertEqual(evaluate("-(10^20) / 7"), -14285714285714285714)
        self.assertEqual(evaluate("(10^20 + 1) % 7"), (10**20 + 1) % 7)
        self.assertEqual(evaluate("-(10^20 + 1) % 7"), -((10**20 + 1) % 7))
        self.assertEqual(evaluate("10^400 / (10^399 + 1)"), 9)

    def test_zero_power(self):
        self.assertEqual(evaluate("0^0"), 1)
        self.assertEqual(evaluate("(-5)^0"), 1)

    def test_leading_zeros(self):
        self.assertEqual(evaluate("007 + 1"), 8)


class TestErrors(unittest.TestCase):
    def assertEvalError(self, expr):
        with self.assertRaises(EvalError, msg=repr(expr)):
            evaluate(expr)

    def test_arithmetic_errors(self):
        for bad in ["1/0", "5 % 0", "1 / (2 - 2)", "2^-1", "(-2)^-1", "0^-1", "2^-(1)"]:
            self.assertEvalError(bad)

    def test_no_unary_plus(self):
        for bad in ["+3", "2 * +3", "(+3)", "2^+1", "1 - +1"]:
            self.assertEvalError(bad)

    def test_syntax_errors(self):
        for bad in ["   ", "2 3", "2(3)", "(1)(2)", "()", "* 2", "1 + 2)", "((1)", "2^",
                    "-", "2 ** 3", "3 = 3"]:
            self.assertEvalError(bad)


if __name__ == "__main__":
    unittest.main()
