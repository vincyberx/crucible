# Task: final league table with head-to-head tiebreakers

Eight clubs played a single round-robin league: every pair of clubs met exactly once, for
28 matches in total. Each result below is written `Home X–Y Away`, where X is the home
team's goals and Y the away team's goals.

| # | Match | # | Match |
|---|-------|---|-------|
| 1 | Kestrel 0–2 Lowfield | 15 | Kestrel 3–0 Westbury |
| 2 | Pinecrest 2–1 Kestrel | 16 | Westbury 1–0 Lowfield |
| 3 | Oakham 2–1 Ironbridge | 17 | Oakham 1–1 Ravenmoor (see decision 1) |
| 4 | Ravenmoor 2–2 Ironbridge | 18 | Pinecrest 0–2 Westbury |
| 5 | Bramley 0–1 Ironbridge | 19 | Pinecrest 1–1 Bramley |
| 6 | Bramley 3–1 Kestrel | 20 | Ironbridge 2–3 Lowfield |
| 7 | Ironbridge 1–1 Pinecrest | 21 | Lowfield 0–3 Bramley |
| 8 | Kestrel 2–1 Ravenmoor | 22 | Pinecrest 1–1 Lowfield |
| 9 | Westbury 0–0 Ironbridge | 23 | Lowfield 0–2 Ravenmoor |
| 10 | Oakham 2–1 Lowfield | 24 | Ravenmoor 3–2 Bramley |
| 11 | Oakham 0–1 Bramley | 25 | Pinecrest 1–3 Ravenmoor |
| 12 | Oakham 1–1 Pinecrest | 26 | Ravenmoor 3–2 Westbury |
| 13 | Oakham 0–0 Westbury | 27 | Oakham 1–1 Kestrel |
| 14 | Kestrel 0–1 Ironbridge | 28 | Westbury 1–1 Bramley |

## Disciplinary decisions (both are final)

1. Match 17 finished 1–1 on the pitch, but Oakham fielded an ineligible player and the
   match was **awarded 0–3 to Ravenmoor**. The awarded result replaces the on-pitch result
   for every purpose: points, goals, and every head-to-head criterion.
2. Bramley has **2 points deducted** (administrative sanction). The deduction applies only
   to the points total used in step 1 below. Head-to-head criteria are computed from match
   results alone, so the deduction plays no part in them.

## Ranking rules

A win is worth 3 points, a draw 1 point, a loss 0 points.

**Step 1.** Clubs are ranked by total points (after the deduction), highest first.

**Step 2.** If two or more clubs have the same total points, they are ranked among
themselves by the following criteria, applied in this order:

- **(a)** points obtained in the matches played between the clubs in question;
- **(b)** goal difference in the matches played between the clubs in question;
- **(c)** goals scored in the matches played between the clubs in question.

**Step 3 (re-application).** If, after (a), (b) and (c) have all been applied to a set of
clubs, some (but not all) of those clubs are still level on all three, then (a), (b) and
(c) are applied again, from the start, to each group of still-level clubs on its own,
using only the matches played between the clubs of that group. Repeat this for any group
that is still level after a re-application, for as long as it keeps separating clubs.

**Step 4.** If (a), (b) and (c) do not separate a set of clubs at all (every club of the
set is level on all three, whether at the first application or at a re-application),
that set is ranked by:

- **(d)** goal difference in all league matches;
- **(e)** goals scored in all league matches;
- **(f)** drawing of lots.

**Question:** what is the final league table, from 1st place to 8th place?

## Deliverable

Write your reasoning to `ANSWER.md` in the current directory. The file must end with a
final line of exactly this form, listing all eight club names from 1st to 8th, separated by
commas with no spaces, e.g. `ANSWER: Kestrel,Oakham,Bramley,Westbury,Lowfield,Pinecrest,Ironbridge,Ravenmoor`:

```
ANSWER: <value>
```
