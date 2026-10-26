# Task: league table with head-to-head tie-breaks

The current directory is a small Python 3 project (standard library only).
`league.py` contains a function `standings(matches)` that ranks the teams of a league. The
current implementation breaks ties on points with overall goal difference, which is not
what the competition rules say. Fix it so that it follows the specification below exactly.

Modify the files in the current directory so that every requirement below is met.
The deliverable is the code in place. You may add tests; do not delete the existing ones.
The existing tests run with `python3 -m unittest discover -s tests -q` from this directory.

## Specification of `standings(matches)`

- `matches` is a list of tuples `(home, away, home_goals, away_goals)`: two different
  team names (non-empty strings) and two integers `>= 0`. Two teams may meet any number of
  times, including never. The teams of the league are exactly the teams that appear in
  `matches`.
- Return the list of all team names, ranked from first to last.
- A win is worth 3 points, a draw 1 point, a loss 0 points. Goal difference is goals scored
  minus goals conceded.

**Ranking.** Teams are ranked by points, higher first. Teams that are level on points are
ordered among themselves by the tie-break procedure below, applied separately to each set
of teams that are level on points.

**Tie-break procedure for a set S of teams.**

1. *Head-to-head.* Build a mini-table from only the matches in which **both** teams belong
   to S (a team with no such match has 0 in every column). Order the teams of S by these
   criteria, in this order, higher first on each:
   (a) mini-table points, (b) mini-table goal difference, (c) mini-table goals scored.
2. *Re-application.* If step 1 separates at least one team of S from the others but leaves
   some teams level with each other on all of (a), (b) and (c), each such set of
   still-level teams is ordered by applying this whole procedure again, from step 1, to
   that set on its own: its new mini-table counts only the matches among the teams of that
   set. This repeats for as many rounds as needed.
3. *Overall.* If step 1 does not separate the teams of S at all (every team of S is level
   with every other on (a), (b) and (c)), order S by (d) goal difference in all matches,
   then (e) goals scored in all matches, higher first on both, and then (f) team name in
   ascending order (Python's default string comparison). Step 3 is final: it never sends
   any team back to step 1.
