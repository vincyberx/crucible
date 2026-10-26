# Crucible benchmark tasks

15 original tasks (5 code, 5 reason, 5 write) for checking whether Crucible beats a
single-shot answer from the same model. Every task has an objectively correct outcome, and
each one has a trap that a single careful-looking pass tends to fall into (`why_hard`).

## Layout

Every task lives in `<id>/` and has:

- `meta.json`: `id`, `kind` (`code` | `reason` | `write`), `title`, `why_hard`, plus the
  extra keys for its kind (below).
- `task.md`: the exact, self-contained prompt for the agent under test, including where
  the deliverable goes.

### kind = code

- `workspace/`: starter project, Python 3 standard library only. The agent runs inside a
  copy of this directory and edits the code in place. Visible tests in `workspace/tests/`
  cover the happy path only.
- `hidden/tests_hidden/`: hidden `unittest` tests for the edge cases that `task.md` states
  explicitly (and nothing else).
- `reference/`: a correct implementation, with the same paths as the workspace module.
- Extra `meta.json` keys: `test_cmd` (visible tests) and `hidden_cmd` (hidden tests).
  After the agent finishes, the runner copies `hidden/*` into the workspace root and
  runs `hidden_cmd` from there.

### kind = reason

- A single verifiable answer. The agent writes its reasoning to `ANSWER.md`, ending with
  a final line `ANSWER: <value>`.
- `solve.py`: a stdlib-only exact or brute-force solver that prints the canonical answer.
- Extra `meta.json` keys: `answer` (the output of `solve.py`) and `answer_type`
  (`integer` | `string` | `set`; for `set` the value is comma-separated and order does
  not matter).

### kind = write

- The agent writes the deliverable to `ANSWER.md`.
- `rubric.md`: 8 numbered pass/fail criteria, each checkable from the text alone
  (counts, presence or absence of something, consistency with the given facts).

## Tasks

| id | kind | title | why_hard |
|----|------|-------|----------|
| code-01 | code | Union of intervals with open/closed bounds | Merging whenever next.start <= current.end ignores bracket types: intervals that are both open at a shared point get glued, empty degenerate intervals are kept, and "closed wins" at shared endpoints is lost. |
| code-02 | code | Largest-remainder money allocation, exact and deterministic | Floats and round() look fine on small amounts, but huge totals lose exactness, and Python's floor on negative totals hands the extra cents to the wrong recipients. |
| code-03 | code | LRU cache with time-to-live, exact eviction semantics | An OrderedDict cache evicts a live LRU entry while an expired one is still stored, uses <= instead of < at the expiry boundary, lets reads extend lifetime, and lets `in` change recency. |
| code-04 | code | Template renderer with escapes, nested paths and defaults | `value or default` swallows 0/""/None/False, the default gets split on every `|`, global `{{`/`}}` pre-replacement breaks `{{{a}}}`, and path validation is skipped. |
| code-05 | code | Version precedence with pre-releases and build metadata | Common cases pass while the spelled-out details fail: numeric vs alphanumeric identifiers, shorter pre-release first, case-sensitive ASCII order, hyphens inside identifiers, build metadata, stable sort, validation. |
| reason-01 | reason | Rail pass expiry with travel days and a validity cap | The activation date is a Sunday, 2028 is a leap year, one holiday falls on a Sunday (no double count), and the 50-day cap must be checked. |
| reason-02 | reason | Order total with promotion, per-line VAT and half-up rounding | Banker's rounding or floats drift by a cent on several half-cent lines, and checking the free-shipping threshold before the discount or with the gift card included wrongly makes shipping free. |
| reason-03 | reason | Knights and knaves with counts and a conditional | Exclusive "or", leaving the speaker out of the count, or reading the conditional as "iff" each gives a different self-consistent answer. |
| reason-04 | reason | Take-away game with two losing conditions | Defaulting to normal play, or forgetting that being stuck with one stone also loses, gives a plausible but wrong sum. |
| reason-05 | reason | PIN blocklist with overlapping rules | Six overlapping rules invite double counting, and it is easy to forget 29 February in a leap year or the inclusive year range. |
| write-01 | write | Release notes from a messy commit log | A reverted feature and its follow-up fix, a fix to a feature new in this release, a codename inside a valid fix, and a 140-word cap. |
| write-02 | write | Incident summary from raw channel notes | Mixed CEST/UTC timestamps (49-minute impact window), an early ~3,000 estimate vs the final 2,371, blameless naming, and P1-only action items. |
| write-03 | write | Dated zero-downtime migration plan | The one-deploy-per-day limit, Tuesday-only lock windows and the 7-day gap push completion to 2026-11-24; 2026-11-17 is the tempting wrong date. |
| write-04 | write | Price-change email to existing customers | Computing EUR 9.00 and 2 Dec 2026, keeping annual subscribers on EUR 84 without mentioning 94.50, leaving out the unapproved free month and competitor line, and staying within 120-180 words. |
| write-05 | write | Vendor recommendation memo for the CFO | The cheapest vendor fails EU residency in a footnote, and leaving out Brevix's month-13 discount (or applying it to all 36 months) changes the winner or the figure. |
| code-06 | code | Minimum-raggedness paragraph wrapping with an exact tie rule | Greedy filling is not optimal and charging the last line changes the answer; the usual forward DP (best cost for each prefix, first candidate kept on ties) returns a minimum-cost layout but not the one the tie rule asks for, because breaking ties locally on the last break orders layouts from the end, not from the first line. |
| code-07 | code | League table with re-applied head-to-head tie-breaks | Sorting by one key tuple (points, head-to-head over the whole points-level group, overall goal difference, name) passes every two-team tie but is wrong once three or more teams are level: the mini-table must be rebuilt for each still-level subset, possibly over several rounds, while a split on overall goal difference or goals scored must never restart the head-to-head step. |
| code-08 | code | Exact integer expression evaluator with power, unary minus and truncating division | Small positive cases pass with almost any parser, but the spec fixes semantics that differ from habit: right-associative ^, unary minus looser than ^ yet allowed right after ^, no unary plus, and C-style truncating / and % on arbitrary-size integers, where the usual int(a / b) goes through a float and is wrong (or overflows) on big numbers while Python's // and % floor instead of truncating. |
| code-09 | code | Cron next fire time with the day-of-month / day-of-week OR rule | Most of the spec matches common cron knowledge, but the day rule turns on whether a field's text starts with '*', not on whether it equals '*' or matches every day: '*/2' or '*/7' keep the AND rule. On top: weekday numbering (Sunday 0 and 7, while datetime.weekday() has Monday 0), '*/S' starting at the field minimum (day 1, month 1), strictly-later with seconds dropped, leap days including 2100, and a None answer that a minute-by-minute scan cannot reach quickly. |
| reason-06 | reason | League table with recursive head-to-head re-application | The awarded 0-3 and Bramley's deduction create a four-way tie on 9 points that needs two nested re-applications (4 clubs -> 3 -> 2, the last pair decided by its direct match) and a three-way tie on 7 that criterion (b) settles across all three clubs. Each tempting shortcut gives a different table: no re-application (straight to overall goal difference) puts Bramley 2nd; only one re-application swaps Oakham and Ironbridge; re-applying as soon as (a) splits a set (instead of after (a)-(c) on the whole set) swaps Lowfield and Pinecrest; goal difference before head-to-head, the on-pitch 1-1 or ignoring the deduction each give yet another order. |
| reason-07 | reason | Two-week payroll with daily, weekly, seventh-day and holiday overtime | Every rule interacts with another. Shifts 4 and 10 must be split at midnight (the first 7 hours of the holiday come from shift 10). Holiday hours that are daily-regular still count toward the weekly 40, so week 2 passes 40 on Saturday 14. Monday 9 is the 7th consecutive working day but R5 applies only to Sunday 15, the one week with all seven days worked. Sunday 15's hours past 40 are already 1.5x, so a weekly premium added on top pays them twice. The holiday's hours past the 12th go to 2x, never stacked. Tempting misreadings: no midnight split 369920; seventh-day premium from Monday 9 onward 430080 (Monday 9 only: 390400); holiday hours left out of the 40: 377600; weekly premium computed as (regular hours - 40) and added on top: 390400; every hour counting toward the 40: 398080; holiday 1.75x beating the 2x hour: 379520; multipliers multiplied together: 395520. |
| reason-08 | reason | Round-robin scheduler with I/O queue, context switches and simultaneous events | Four instants have simultaneous events that rule 7 orders: at t=6 A's I/O return queues ahead of B's arrival; at t=13 D's arrival goes ahead of the preempted B; at t=40 and t=56 an I/O return goes ahead of the preempted process. A's first burst ends exactly at quantum expiry, so it goes to I/O, not to the ready queue. At t=6 A is dispatched without a context switch even though the CPU was idle, because A was the last process to run. At t=36 C must wait for the single I/O device. Each tempting misreading changes the times: preempted process queued ahead of newcomers gives A=17,B=38,C=52,D=60,E=57; arrivals queued before I/O returns gives A=34,B=36,C=50,D=63,E=58; a switch on every dispatch gives A=18,B=43,C=50,D=63,E=59; a switch after an idle gap gives A=18,B=43,C=50,D=63,E=58; parallel I/O gives A=17,B=42,C=45,D=62,E=57; a free first dispatch gives A=16,B=37,C=51,D=58,E=60. |
| reason-09 | reason | Transit fares with transfers, service-day caps and end-of-day refunds | Order of application decides the total. The refund of ride 27 comes only after its service day, which includes ride 29 at 03:20 on Thursday, so ride 28 stays capped at 0. In week 1 the refunded 320 stops counting toward the weekly cap, so later rides fill the cap again. Rides 14 and 29 are charged 0 by caps but still start journeys, so rides 15 and 30 are transfers across a service-day or service-week boundary. The 90-minute window runs from the journey's first ride and is inclusive (ride 17), with at most 2 transfers (ride 24). Upgrades are priced with the first ride's peak status (ride 17). The cheaper-of-two discount gives 210 rather than 220 for off-peak 2-zone rides. Tempting misreadings: window measured from the previous ride 4180; strict < 90 4380; no transfer limit 4090; upgrade at the transfer's own peak status 4260; discounts combined 4080; calendar days/weeks for caps 4700; capped rides not starting journeys (or journeys cut at 04:00) 4630; refund applied immediately 4460; refunded amount still counting toward the weekly cap 3980; refunding the full fare 4060. |
