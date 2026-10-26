# Task: split an amount of money proportionally, to the cent

The current directory is a small Python 3 project (standard library only).
`allocate.py` contains `allocate(total, weights)`, which splits an integer amount of cents
across recipients in proportion to integer weights. The current implementation is a quick
draft that does not follow the rules below. Fix it.

Modify the files in the current directory so that every requirement below is met.
The deliverable is the code in place. You may add tests; do not delete the existing ones.
The existing tests run with `python3 -m unittest discover -s tests -q` from this directory.

## Specification of `allocate(total: int, weights: list[int]) -> list[int]`

1. `total` is an integer number of cents and may be positive, zero or negative.
   `weights` is a list of integers.
2. Raise `ValueError` if `weights` is empty, if any weight is negative, or if all weights
   are zero.
3. The result is a list of integers with the same length as `weights` whose sum is
   **exactly** `total`.
4. For `total >= 0` (with `W = sum(weights)`):
   - every entry first receives `floor(total * w_i / W)`;
   - the cents still missing (call that number `r`) are then handed out one cent each to
     the `r` entries with the **largest remainder** `(total * w_i) mod W`;
   - when remainders are equal, the entry with the **lower index** gets the cent first.
5. For `total < 0` the result is the element-wise negation of `allocate(-total, weights)`.
   Example: `allocate(-100, [1, 1, 1]) == [-34, -33, -33]`.
6. The computation must be exact for arbitrarily large integers (amounts like `10**20 + 1`
   must still be split correctly). Do not rely on floating point.
7. Examples: `allocate(100, [1, 1, 1]) == [34, 33, 33]`, `allocate(10, [1, 2, 3]) == [2, 3, 5]`,
   `allocate(5, [0, 0, 3]) == [0, 0, 5]`.
