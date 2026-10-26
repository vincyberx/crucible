# Task: union of intervals with open and closed bounds

The current directory is a small Python 3 project (standard library only).
`intervals.py` contains a function `union(specs)` that is supposed to compute the
union of a list of intervals, but it ignores most of the rules below. Fix it.

Modify the files in the current directory so that every requirement below is met.
The deliverable is the code in place. You may add tests; do not delete the existing ones.
The existing tests run with `python3 -m unittest discover -s tests -q` from this directory.

## Specification of `union(specs: list[str]) -> list[str]`

1. **Input format.** Each element of `specs` is a string: a left bracket (`[` = closed,
   `(` = open), an integer start, a comma, an integer end, and a right bracket (`]` = closed,
   `)` = open). Integers may be negative. Spaces may appear around either integer
   (e.g. `"[ -3 , 4 )"`). Any other shape (missing bracket, non-integer number, other
   bracket characters, ...) raises `ValueError`.
2. **start > end** raises `ValueError`.
3. **Real-number semantics.** An interval is the set of *real* numbers between its endpoints,
   not a set of integers. So `[1,2]` and `[3,4]` are disjoint and must stay separate, while
   `[1,2)` and `[2,3]` together cover everything from 1 to 3.
4. **Degenerate intervals.** When start == end: `[a,a]` is the single point `a` (non-empty);
   `[a,a)`, `(a,a]` and `(a,a)` are empty and contribute nothing to the union.
5. **Touching endpoints.** Two pieces that meet at a value `x` belong to the same output
   interval if and only if `x` itself is covered by at least one of the input intervals.
   Examples: `[1,5)` and `(5,7]` stay separate (5 is not covered); `[1,5)` and `[5,7]`
   become `[1,7]`; `[1,5]` and `(5,7]` become `[1,7]`; `[1,5)`, `[5,5]`, `(5,7]` become `[1,7]`.
6. **Bound inclusiveness.** An endpoint of an output interval is closed if the endpoint value
   belongs to the union, open otherwise. Examples: `[1,5)` and `[2,5]` give `[1,5]`;
   `(1,3]` and `[1,2]` give `[1,3]`.
7. **Output.** A list of canonical strings with no spaces (e.g. `"[-3,6]"`, `"(1,5)"`),
   sorted by position on the real line, minimal: no two output intervals could be merged
   into one. Empty input (or input made only of empty intervals) returns `[]`.
   Duplicate inputs are allowed.
