# Rubric: write-03 (migration plan)

Each criterion is pass/fail and checkable from the text of `ANSWER.md`.

1. Each of S1-S9 appears exactly once as a scheduled step with a date (`YYYY-MM-DD`) and a
   start time in UTC; no step starts before 2026-11-09 09:00 UTC.
2. Precedence is respected (by date and time): S8 before S1, S3, S5 and S7; S1 before S2;
   S2 before S3; S9 starts at least 2 hours after S3 starts; S9 before S4 and S5; S4 and
   S5 before S6; S6 before S7.
3. The deploys S2, S4 and S6 are each on a Monday-Thursday, start between 09:00 and
   16:00 UTC, and fall on three different dates.
4. S5 and S7 are each on a Tuesday with a start time between 02:00 and 03:00 UTC, in two
   different windows.
5. S7's date is at least 7 calendar days after S6's date.
6. S7 is scheduled on **2026-11-24** and the final line is `Completion: 2026-11-24`
   (the earliest feasible completion: S2 Mon 11-09, S5 Tue 11-10 window, S4 Tue 11-10,
   S6 Wed 11-11, so S7 cannot be before Wed 11-18 and the next window is Tue 11-24).
7. S7 is explicitly marked as irreversible.
8. The file has at most 300 words, counting whitespace-separated tokens that contain at least one letter or digit (a lone `-` or `**` is not a word).
