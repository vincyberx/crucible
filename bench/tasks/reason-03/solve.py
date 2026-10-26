"""Exact solver for reason-03: enumerate all 2^6 assignments and check uniqueness."""

from itertools import product

NAMES = "ABCDEF"


def implies(p, q):
    return (not p) or q


def statements(k):
    a, b, c, d, e, f = k
    knights = sum(k)
    knaves = 6 - knights
    return [
        (not c) or e,                 # A
        knights == 4,                 # B
        knaves >= 4,                  # C
        f != b,                       # D
        implies(c, d),                # E
        sum([a, c, e]) == 1,          # F
    ]


def main():
    solutions = []
    for k in product([True, False], repeat=6):
        if all(s == speaker for s, speaker in zip(statements(k), k)):
            solutions.append(k)
    assert len(solutions) == 1, solutions
    print(",".join(n for n, is_knight in zip(NAMES, solutions[0]) if is_knight))


if __name__ == "__main__":
    main()
