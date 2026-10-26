"""Integer expression evaluator."""


class EvalError(Exception):
    pass


def _tokenize(expr):
    tokens = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch.isspace():
            i += 1
        elif ch.isdigit():
            j = i
            while j < len(expr) and expr[j].isdigit():
                j += 1
            tokens.append(int(expr[i:j]))
            i = j
        elif ch in "+-*/%^()":
            tokens.append(ch)
            i += 1
        else:
            raise EvalError("unexpected character %r" % ch)
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def expr(self):
        value = self.term()
        while self.peek() in ("+", "-"):
            op = self.next()
            rhs = self.term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def term(self):
        value = self.factor()
        while self.peek() in ("*", "/", "%"):
            op = self.next()
            rhs = self.factor()
            if op == "*":
                value = value * rhs
            elif op == "/":
                value = int(value / rhs)
            else:
                value = value - rhs * int(value / rhs)
        return value

    def factor(self):
        value = self.unary()
        while self.peek() == "^":
            self.next()
            value = int(value ** self.unary())
        return value

    def unary(self):
        if self.peek() in ("-", "+"):
            op = self.next()
            value = self.unary()
            return -value if op == "-" else value
        return self.atom()

    def atom(self):
        tok = self.next()
        if isinstance(tok, int):
            return tok
        if tok == "(":
            value = self.expr()
            if self.next() != ")":
                raise EvalError("missing ')'")
            return value
        raise EvalError("unexpected token %r" % (tok,))


def evaluate(expr):
    parser = _Parser(_tokenize(expr))
    value = parser.expr()
    if parser.pos != len(parser.tokens):
        raise EvalError("unexpected trailing input")
    return value
