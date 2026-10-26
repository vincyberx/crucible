# Task: paragraph wrapping with minimum raggedness

The current directory is a small Python 3 project (standard library only).
`wrap.py` contains a function `wrap(text, width)` that splits a paragraph into lines. The
current implementation fills each line greedily, which does not follow the specification
below. Fix it so that it follows the specification exactly.

Modify the files in the current directory so that every requirement below is met.
The deliverable is the code in place. You may add tests; do not delete the existing ones.
The existing tests run with `python3 -m unittest discover -s tests -q` from this directory.

## Specification of `wrap(text, width)`

- `width` must be an `int` `>= 1`; otherwise raise `ValueError`.
- The words of the paragraph are `text.split()` (maximal runs of non-whitespace characters).
  If there are no words, return `[]`.
- A *layout* splits the sequence of words, in their original order, into one or more
  lines. Every line holds at least one word, and the words of a line are joined by exactly
  one space. The *length* of a line is its number of characters (words plus the single
  spaces between them).
- A line is *allowed* if its length is at most `width`, or if it consists of a single word
  (a word longer than `width` is never split: it sits alone on its own line).
- The *cost* of a line is:
  - `0` for the last line of the layout;
  - `0` for a line made of a single word longer than `width`;
  - otherwise `(width - length) ** 2`.

  The cost of a layout is the sum of the costs of its lines.
- `wrap` returns the layout, among all layouts whose lines are all allowed, with the
  **minimum total cost**, as a list of strings (one string per line, no trailing spaces).
- **Ties.** If several layouts have the same minimum total cost, return the one whose first
  line contains the most words. If the first lines contain the same number of words,
  compare the second lines in the same way, and so on, line by line, until one layout has
  more words on a line than the other.

Paragraphs of a few thousand words must be handled in seconds, not minutes (trying every
possible layout is not an option).
