# Task: compare and sort version strings with pre-releases and build metadata

The current directory is a small Python 3 project (standard library only).
`versions.py` has `compare(a, b)` and `sort_versions(versions)`, but the current draft only
understands plain `X.Y.Z` strings. Implement the full rules below.

Modify the files in the current directory so that every requirement below is met.
The deliverable is the code in place. You may add tests; do not delete the existing ones.
The existing tests run with `python3 -m unittest discover -s tests -q` from this directory.

## Version syntax

A version string is `MAJOR.MINOR.PATCH`, optionally followed by `-PRERELEASE`, optionally
followed by `+BUILD` (in that order). Nothing else is allowed: no leading `v`, no spaces,
no fewer or more than three core numbers.

- `MAJOR`, `MINOR`, `PATCH`: non-empty ASCII digit strings without leading zeros
  (`0` is fine, `01` is invalid).
- `PRERELEASE`: one or more identifiers separated by `.`. Each identifier is non-empty and
  made only of ASCII letters, ASCII digits and `-`. An identifier made only of digits is
  *numeric* and must not have a leading zero (`0` is fine, `007` is invalid); any other
  identifier is *alphanumeric* (e.g. `alpha`, `rc-1`, `0a`).
- `BUILD`: one or more identifiers separated by `.`, each non-empty and made only of ASCII
  letters, ASCII digits and `-`. Leading zeros are allowed here.
- The pre-release starts at the first `-` after PATCH; any later `-` belongs to the
  identifiers. The build starts at the first `+`.

Any invalid string passed to `compare` or `sort_versions` raises `ValueError`.

## Precedence

1. Compare MAJOR, then MINOR, then PATCH, numerically.
2. If those are equal, a version **with** a pre-release has **lower** precedence than the
   same version without one (`1.0.0-rc.1 < 1.0.0`).
3. Two pre-releases are compared identifier by identifier, left to right:
   - two numeric identifiers compare numerically;
   - two alphanumeric identifiers compare lexically by ASCII code (so `Z < a`);
   - a numeric identifier always has lower precedence than an alphanumeric one;
   - if all identifiers are equal up to the length of the shorter pre-release, the one with
     fewer identifiers has lower precedence.
4. Build metadata is ignored for precedence.

## Functions

- `compare(a: str, b: str) -> int`: returns `-1` if `a` has lower precedence than `b`,
  `1` if higher, `0` if equal precedence (e.g. `compare("1.0.0+a", "1.0.0+b") == 0`).
- `sort_versions(versions: list[str]) -> list[str]`: returns a new list sorted from lowest
  to highest precedence. Versions with equal precedence keep their original relative order.
