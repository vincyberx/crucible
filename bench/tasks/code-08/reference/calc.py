"""Integer expression evaluator (reference implementation).

Grammar, loosest to tightest:
    expr  := term (('+' | '-') term)*
    term  := unary (('*' | '/' | '%') unary)*
    unary := '-' unary | power
    power := atom ('^' unary)?          # right operand parsed at unary level: right-assoc
    atom  := NUMBER | '(' expr ')'
"""


class EvalError(Exception):
    pass


def _tokenize(expr):
    tokens = []
    i, n = 0, len(expr)
    while i < n:
        ch = expr[i]
        if ch.isspace():
            i += 1
        elif "0" <= ch <= "9":
            j = i
            while j < n and "0" <= expr[j] <= "9":
                j += 1
            tokens.append(("num", int(expr[i:j])))
            i = j
        elif ch in "+-*/%^()":
            tokens.append(("op", ch))
            i += 1
        else:
            raise EvalError("unexpected character %r" % ch)
    return tokens


def _tdiv(a, b):
    if b == 0:
        raise EvalError("division by zero")
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def take_op(self, ops):
        kind, val = self.peek()
        if kind == "op" and val in ops:
            self.pos += 1
            return val
        return None

    def expr(self):
        value = self.term()
        while True:
            op = self.take_op("+-")
            if op is None:
                return value
            rhs = self.term()
            value = value + rhs if op == "+" else value - rhs

    def term(self):
        value = self.unary()
        while True:
            op = self.take_op("*/%")
            if op is None:
                return value
            rhs = self.unary()
            if op == "*":
                value = value * rhs
            elif op == "/":
                value = _tdiv(value, rhs)
            else:
                value = value - rhs * _tdiv(value, rhs)

    def unary(self):
        if self.take_op("-"):
            return -self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.take_op("^"):
            exp = self.unary()
            if exp < 0:
                raise EvalError("negative exponent")
            return base ** exp
        return base

    def atom(self):
        kind, val = self.peek()
        if kind == "num":
            self.pos += 1
            return val
        if kind == "op" and val == "(":
            self.pos += 1
            value = self.expr()
            if not self.take_op(")"):
                raise EvalError("missing ')'")
            return value
        raise EvalError("expected a number or '(' at token %d" % self.pos)


def evaluate(expr):
    parser = _Parser(_tokenize(expr))
    value = parser.expr()
    if parser.pos != len(parser.tokens):
        raise EvalError("unexpected token at %d" % parser.pos)
    return value
