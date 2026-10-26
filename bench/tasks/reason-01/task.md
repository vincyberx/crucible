# Task: when does the rail pass run out?

A regional rail operator sells the **Flex-40** pass. Its rules are:

1. A *travel day* is a calendar day that is **not a Sunday** and **not an operator holiday**
   (list below). On days that are not travel days the pass is not accepted and nothing is
   consumed.
2. The pass is activated on **Sunday 27 February 2028**. From the activation date onward,
   every travel day consumes one of the pass's **40** days, whether or not the holder
   actually rides that day.
3. Independently of rule 2, the pass is valid for at most **50 calendar days**, where the
   activation date is calendar day 1. After calendar day 50 the pass is void.
4. The pass can be used on a date only if that date is a travel day, it is within the
   50-calendar-day validity, and no more than 40 travel days have been consumed up to and
   including that date.

Operator holidays: 6 January 2028, 1 March 2028, 19 March 2028, 14 April 2028,
17 April 2028, 25 April 2028, 1 May 2028.

Use the real Gregorian calendar.

**Question:** what is the last date on which the pass can be used?

## Deliverable

Write your reasoning to `ANSWER.md` in the current directory. The file must end with a
final line of exactly this form (date as `YYYY-MM-DD`):

```
ANSWER: <value>
```
