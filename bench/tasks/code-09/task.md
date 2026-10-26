# Task: next fire time of a cron expression

The current directory is a small Python 3 project (standard library only).
`cron.py` contains a function `next_fire(expr, after)` that computes when a five-field cron
expression fires next. The current implementation has several bugs. Fix it so that it
follows the specification below exactly.

Modify the files in the current directory so that every requirement below is met.
The deliverable is the code in place. You may add tests; do not delete the existing ones.
The existing tests run with `python3 -m unittest discover -s tests -q` from this directory.

## Specification of `next_fire(expr, after)`

**Expression.** `expr` has exactly five fields separated by whitespace, in this order:

| field        | allowed values                                               |
|--------------|--------------------------------------------------------------|
| minute       | 0–59                                                         |
| hour         | 0–23                                                         |
| day of month | 1–31                                                         |
| month        | 1–12                                                         |
| day of week  | 0–7, where 0 and 7 both mean Sunday, 1 Monday, …, 6 Saturday |

Each field is a comma-separated list of one or more items. An item is one of:

- `*`: every allowed value of the field;
- `N`: the single value N;
- `A-B`: every value from A to B inclusive (A must not be greater than B);
- `*/S`: the field's minimum allowed value, then every S-th value after it, up to the
  field's maximum (S >= 1);
- `A-B/S`: A, then every S-th value after it, up to B (A <= B, S >= 1).

Numbers are written with ASCII digits only. An expression that does not have exactly this
shape raises `ValueError`. In particular: a number of fields other than five, an empty
item, an item that is none of the five forms above, a value outside the field's allowed
values, `A > B`, a step of 0, a step after a single number (`N/S`), or any other character
(names such as `MON` or `JAN` are not supported).

**Matching.** A date and time matches the expression when its minute, its hour and its
month are each in the corresponding field, and its date satisfies the day rule:

- A day field (day of month, day of week) is *unrestricted* if its first character is `*`,
  and *restricted* otherwise.
- If **both** day fields are restricted, the date satisfies the day rule when its day of
  the month is in the day-of-month field **or** its weekday is in the day-of-week field.
- Otherwise, the date satisfies the day rule when its day of the month is in the
  day-of-month field **and** its weekday is in the day-of-week field.

**Result.** `after` is a naive `datetime.datetime` (no time zones, no daylight saving).
`next_fire` returns the earliest matching `datetime.datetime` that is **strictly later**
than `after` and has `second == 0` and `microsecond == 0`. If no such time exists before
`datetime.datetime(after.year + 11, 1, 1)`, it returns `None`. Each call must finish in a
fraction of a second, including when the answer is `None`.
