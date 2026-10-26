# Task: two-week payroll with overlapping overtime rules

An hourly employee is paid a **base rate of €25.60 per hour**. Compute the employee's gross
pay for the two-week pay period from Monday 2 November 2026 to Sunday 15 November 2026.

## Timesheet

All times are local, on a 24-hour clock. A shift runs from its start time up to its end
time. Unpaid breaks are not hours worked. The employee did not work at any other time in
the pay period.

| Shift | Start | End | Unpaid break |
|-------|-------|-----|--------------|
| 1 | Tue 3 Nov 07:00 | Tue 3 Nov 17:30 | 12:00–12:30 |
| 2 | Wed 4 Nov 08:00 | Wed 4 Nov 16:00 | none |
| 3 | Thu 5 Nov 06:00 | Thu 5 Nov 20:30 | 13:00–13:30 |
| 4 | Fri 6 Nov 20:00 | Sat 7 Nov 06:00 | none |
| 5 | Sat 7 Nov 14:00 | Sat 7 Nov 22:00 | none |
| 6 | Sun 8 Nov 09:00 | Sun 8 Nov 17:00 | none |
| 7 | Mon 9 Nov 08:00 | Mon 9 Nov 17:00 | none |
| 8 | Tue 10 Nov 08:00 | Tue 10 Nov 16:00 | none |
| 9 | Wed 11 Nov 07:00 | Wed 11 Nov 18:00 | 12:00–13:00 |
| 10 | Thu 12 Nov 22:00 | Fri 13 Nov 07:00 | none |
| 11 | Fri 13 Nov 15:00 | Fri 13 Nov 21:00 | none |
| 12 | Sat 14 Nov 08:00 | Sat 14 Nov 18:30 | 12:30–13:00 |
| 13 | Sun 15 Nov 10:00 | Sun 15 Nov 19:00 | none |

## Pay rules

- **R1. Workweek.** A workweek runs from Monday 00:00 to Sunday 24:00. The pay period
  contains two workweeks: week 1 is 2–8 November, week 2 is 9–15 November. Nothing is
  carried over or averaged from one workweek to the other.
- **R2. Attribution.** Every hour worked belongs to the calendar day in which it is
  actually worked. A shift that crosses midnight is split at midnight.
- **R3. Daily overtime.** Within each calendar day, taking the hours worked in
  chronological order, the first 8 hours are *daily-regular* hours; hours after the 8th, up
  to and including the 12th, qualify for **1.5×**; hours after the 12th qualify for **2×**.
- **R4. Weekly overtime.** Within each workweek, go through its daily-regular hours in
  chronological order. Once 40 daily-regular hours have been counted in that workweek,
  every further daily-regular hour of the same workweek qualifies for **1.5×**. Hours that
  qualify for 1.5× or 2× under R3 never count toward the 40. Whether an hour counts toward
  the 40 depends only on R3: a daily-regular hour counts even if R5 or R6 also applies to it.
- **R5. Seventh consecutive day.** If the employee works on all seven calendar days of a
  workweek, the Sunday of that workweek is its seventh consecutive day: the first 8 hours
  worked on that Sunday qualify for **1.5×**, and every hour after the 8th that Sunday
  qualifies for **2×**. R5 applies in no other situation.
- **R6. Public holiday.** Friday 13 November 2026 is a public holiday. Every hour worked on
  that calendar day qualifies for **1.75×**.
- **R7. Precedence.** An hour may qualify under several rules at once. Each hour is paid
  at the base rate times the single highest multiplier it qualifies for, or at 1× if it
  qualifies for none. Multipliers are never added together or multiplied together.

**Question:** what is the employee's gross pay for the pay period, in euro cents?

## Deliverable

Write your reasoning to `ANSWER.md` in the current directory. The file must end with a
final line of exactly this form, giving the gross pay as an integer number of euro cents
(for example €1,234.56 is written `ANSWER: 123456`):

```
ANSWER: <value>
```
