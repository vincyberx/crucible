# Task: how many PINs survive the blocklist?

A bank uses 4-digit PINs from `0000` to `9999` (leading zeros allowed, so there are 10,000
possible PINs). A PIN is **rejected** if **any** of the following rules applies to it:

- **R1.** All four digits are equal (e.g. `7777`).
- **R2.** The digits are consecutive ascending (each digit is one more than the previous,
  e.g. `2345`) or consecutive descending (each digit is one less than the previous,
  e.g. `6543`). There is no wrap-around: `8901` and `1098` are not consecutive.
- **R3.** Read as `MMDD` (first two digits = month, last two = day), the PIN is a valid
  calendar date in a **leap year** (months `01`-`12`, days from `01` up to the month's
  length; February has 29 days).
- **R4.** Read as `DDMM` (first two digits = day, last two = month), the PIN is a valid
  calendar date in a **leap year** (same rules as R3).
- **R5.** The first two digits are the same as the last two digits, in the same order
  (e.g. `4747`).
- **R6.** The PIN, read as a 4-digit number, is a year from 1940 to 2029 inclusive.

**Question:** how many of the 10,000 PINs are **accepted** (not rejected by any rule)?

## Deliverable

Write your reasoning to `ANSWER.md` in the current directory. The file must end with a
final line of exactly this form (an integer):

```
ANSWER: <value>
```
