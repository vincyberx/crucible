# Task: an exact integer expression evaluator

The current directory is a small Python 3 project (standard library only).
`calc.py` contains a function `evaluate(expr)` that evaluates an arithmetic expression over
integers, and an exception class `EvalError`. The current implementation has several bugs.
Fix it so that it follows the specification below exactly.

Modify the files in the current directory so that every requirement below is met.
The deliverable is the code in place. You may add tests; do not delete the existing ones.
The existing tests run with `python3 -m unittest discover -s tests -q` from this directory.

## Specification of `evaluate(expr)`

`expr` is a string; `evaluate` returns a Python `int`, or raises `EvalError` (the class
defined in `calc.py`). It must never raise any other exception type for a string input.

**Tokens.**
- An integer literal is a run of one or more ASCII digits `0`–`9`; leading zeros are
  allowed (`007` is 7). There are no negative literals: a minus sign is always an operator.
- Operators: `+`, `-`, `*`, `/`, `%`, `^`, and the parentheses `(` and `)`.
- Whitespace (any character for which `str.isspace()` is true) between tokens is ignored.
- Any other character is an error.

**Operators, from the tightest binding to the loosest.**
1. Parentheses.
2. `^` (power). It is **right-associative**: `a ^ b ^ c` means `a ^ (b ^ c)`.
3. Unary minus `-`. It binds **less tightly than `^`**: `-a ^ b` means `-(a ^ b)`.
   A unary minus may appear at the start of the expression, right after `(`, and right
   after any binary operator, **including `^`**; the right operand of `^` may therefore
   start with one or more unary minuses (`a ^ -b` means `a ^ (-b)`). Unary minuses may be
   repeated: `--a` is `a`.
4. `*`, `/`, `%`, left-associative, all with the same precedence.
5. Binary `+` and `-`, left-associative, with the same precedence.

There is no unary plus (`+` is only a binary operator) and no implicit multiplication
(`2(3)` is an error).

**Arithmetic.** Integers have arbitrary size and every result must be exact, however large
the numbers involved.
- `a / b` is the quotient **truncated toward zero**: `7 / 2` is `3`, `-7 / 2` is `-3`.
- `a % b` is the remainder that goes with that quotient, `a - b * (a / b)`; it has the sign
  of `a` (or is 0): `-7 % 2` is `-1`, `7 % -2` is `1`.
- `a ^ b` is `a` raised to the power `b`; `0 ^ 0` is `1`.

**Errors.** Raise `EvalError` for: an empty or whitespace-only expression; an invalid
character; unbalanced parentheses; a missing operand (for example `2 +`, `* 2`, `()`); two
operands in a row (for example `2 3`, `2(3)`, `(1)(2)`); a unary plus; division or
remainder by zero; a negative exponent.
