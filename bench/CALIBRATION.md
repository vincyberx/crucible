# Calibration log

A benchmark task is only useful if a single answer fails it at least some of the time: otherwise a tournament has nothing to win.

## 2026-10-26 · single answer, 2 runs per task, Claude Code headless (`--setting-sources project`)

| task | Sonnet 5.5 | Opus 5.5 |
|---|---|---|
| code-01 … code-05 | 1.00 · 1.00 (all) | 1.00 · 1.00 (all) |
| reason-01 … reason-05 | 1.00 · 1.00 (all) | 1.00 · 1.00 (all) |
| write-01, write-04, write-05 | 1.00 · 1.00 | 1.00 · 1.00 |
| write-02 | 0.88 · 0.75 | 0.88 · 1.00 |
| write-03 | 1.00 · 1.00 | 0.88 · 1.00 |

Cost at list price: Sonnet $2.02 for 30 runs ($0.07 each), Opus $5.08 ($0.17 each).

What failed: 203 words against a 200-word limit; a time range with only one "UTC"; a label not followed by a colon; a plan over 300 words. Every miss is a hard, countable constraint, not a matter of quality.

Conclusions:

- The code and reasoning tasks are too easy for current models: 40 runs out of 40 passed. They need to be replaced with harder ones before the benchmark can say anything about Crucible on code or reasoning.
- The constraint-heavy writing tasks are where single answers slip. Those criteria (word counts, labels, formats) should be scored by a script rather than a model judge.

Note: the word limit was then made explicit (a word is a token with at least one letter or digit, so a lone `-` or `|` does not count) and scored by script. Under that rule two of the misses above disappear (203 → 200 words on write-02; a table at 362 tokens but 291 words on write-03).

## 2026-10-26 · targeted run: write-02 and write-03, Sonnet 5.5, 3 runs per arm

Countable criteria scored by each task's `check.py`, the rest by the blind model judge. The script and the judge agreed on every criterion of all 22 answers collected so far, apart from the two word-rule changes above.

| task | single: all criteria met | Crucible: all criteria met | cost per run (single / Crucible) | calls |
|---|---|---|---|---|
| write-02 | 1 of 3 | 3 of 3 | $0.07 / $0.65 | 5, 7, 5 |
| write-03 | 3 of 3 | 3 of 3 | $0.08 / $0.54 | 5, 5, 5 |

Both single misses on write-02 are the same: the label `Action items (P1):` instead of `Action items:`. In one Crucible run the red team found a real MAJOR flaw (the Summary contradicted the Duration line on start and end times) and the revision fixed it.

Three runs per arm is a hint, not evidence: 1/3 against 3/3 is well within chance. Crucible cost about 8.5× more per run. Total cost of this run: $4.00 at list price.

## 2026-10-26 · write-02, Sonnet 5.5, 10 runs per arm (outcome and test fixed before the run)

Primary outcome: every criterion met. Test: Fisher's exact, two-sided (`bench/stats.py`).

| arm | all criteria met | mean score | cost per run | time per run |
|---|---|---|---|---|
| single | 3 of 10 | 0.912 | $0.07 | 0.2 min |
| Crucible | **10 of 10** | 1.000 | $0.50 | 1.4 min |

**p = 0.0031**: significant at 0.05. Crucible used 5 calls in every run; no revision was needed.

Every single failure is the same one: `Action items (P1):` instead of the required label `Action items:` (7 of 10). None of the 30 Crucible candidates made that mistake, and the red team found nothing above MINOR. So the gain here does not come from choosing among candidates, nor from the red team: it comes from the framing step, where the host turns the task into explicit acceptance checks that every candidate must meet. The next arm to test is a single answer that writes and verifies its own checklist (one call), to see how much of the gain survives without the tournament.

## 2026-10-26 · write-02, third arm: checklist (10 runs, Sonnet 5.5)

The `checklist` arm is one call: the model writes the task's acceptance checks to a file, answers, then checks its answer against every item and fixes what fails. It is Crucible's framing step without the tournament.

| arm | all criteria met | cost per run | time per run |
|---|---|---|---|
| single | 3 of 10 | $0.07 | 0.2 min |
| checklist | **9 of 10** | $0.08 | 0.3 min |
| Crucible | **10 of 10** | $0.50 | 1.4 min |

- checklist against single: p = 0.0198, significant.
- checklist against Crucible: p = 1.0, no difference this sample can show.

On this task almost all of Crucible's gain comes from writing the acceptance checks down and verifying against them, for about 15% more than a single answer instead of about 7 times more. The tournament has yet to show value of its own: that needs tasks whose failures are wrong reasoning or wrong code, not missed constraints.

## 2026-10-26 · write-02, fourth arm: arena-skill `--quick` (3 runs, Sonnet 5.5)

[arena-skill](https://github.com/Jakeschincariol/arena-skill) at commit `df07b8e`, `--quick` (16 agents, 4 rounds, 91 sub-agent calls), installed only inside each scratch folder.

| arm | all criteria met | cost per run | time per run | sub-agent calls |
|---|---|---|---|---|
| single | 3 of 10 | $0.07 | 0.2 min | 0 |
| checklist | 9 of 10 | $0.08 | 0.3 min | 0 |
| Crucible | 10 of 10 | $0.50 | 1.4 min | 5 |
| arena `--quick` | 3 of 3 | $7.16 | 8.8 min | 91 |

- arena against single: p = 0.070; against checklist and Crucible: p = 1.0. Three runs cannot separate arena from either.
- arena cost about 14× Crucible and about 90× the checklist for the same outcome on this task.
- Among arena's 48 initial competitors (16 per run), 5 had the label mistake (10%), against 7 of 10 plain single answers and 0 of 30 Crucible candidates: arena's strategy cards and its standalone task file already remove most of the error, and the bracket filters the rest.

Total cost of the arena arm: $21.48 at list price.

## 2026-10-26 · harder tasks: code-06..09 and reason-06..09 (Sonnet 5.5)

Traps of substance, not form: optimal line breaking with a tie rule, re-applied head-to-head tiebreaks, operator semantics, the cron day-of-month/day-of-week OR rule, payroll and fare rules whose order matters, a scheduler with simultaneous events. In every code task a careful-looking naive implementation passes the visible tests and fails the hidden ones.

Calibration, single answer, 3 runs each: **23 of 24 correct**. The only miss was reason-06 (1 of 3: head-to-head not re-applied). Cost $3.02.

Three arms on reason-06, 10 runs each:

| arm | correct | cost per run | time per run |
|---|---|---|---|
| single | 10 of 10 | $0.11 | 0.6 min |
| checklist | 9 of 10 | $0.12 | 0.7 min |
| Crucible | 10 of 10 | $0.42 | 1.6 min |

No difference (p = 1.0). The calibration miss was chance: over 13 single runs reason-06 failed once. Cost $6.42.

**Where this leaves the benchmark.** With tools to run code, Sonnet 5.5 almost never gets a precisely specified, self-contained task wrong in substance, even with deliberate traps. The only reliable failures found so far are missed formal constraints, and an explicit checklist fixes those for the price of one call. No tournament (Crucible or arena-skill) has shown a measurable benefit over the checklist on any task here. A tournament can still help where a task is open-ended, underspecified or spread over a large codebase, but those are the cases this kind of benchmark cannot score objectively.

## 2026-10-26 · real bugs from the author's repositories (Sonnet 5.5)

Twelve fixed bugs taken from the git history of four private repositories (a Python voice assistant, a TypeScript live-game backend, two business back-offices): the workspace is the tree just before the fix, with no history, plus a bug report; the hidden test is the test that came with the real fix. Every task was verified: the visible tests pass before the fix, the hidden test fails before and passes after. The tasks are private and kept out of this repository (`bench/private-tasks/`, git-ignored); `bench/run.py --tasks-dir` runs them.

- **Single answer, 2 runs per task: 24 of 24 fixed**, $0.15 and 0.5 minutes per run ($3.59 in all). The session transcripts show no reads of the source repositories (which hold the fixed code), only their virtual environments to run the tests.
- The bug reports give the symptom, a reproduction and the expected values, as a careful teammate would. That makes the bugs well specified, which is the regime where single answers do not fail.
- Functional check of Crucible on two of them (one Python, one TypeScript with jest): level 0 on the TypeScript one passed on the first attempt with its own check script, no sub-agents, $0.23. The forced tournament ran on both with 5 sub-agent calls, worktrees with linked dependencies worked, the red team found nothing, the patch passed the hidden tests: $0.87 to $1.36, 2.5 to 3.3 minutes. On the Python one the level-0 run skipped Crucible altogether ("the cause was clear and the change small") and still fixed the bug; SKILL.md now says to run Crucible whenever the user asked for it.

So far, then: real bugs with clear reports are fixed by a single Sonnet answer every time, and no tournament has room to show a gain. What is left to try is the harder case of bug reports that give only the symptom.

## 2026-10-26 · the same real bugs, symptom-only reports (Sonnet 5.5)

The twelve reports were rewritten to say only what a user sees: the area and the symptom, in plain terms. Removed: reproduction steps and their values, expected values, internal names (classes, functions, fields, constants), and anything that points at the cause. Kept, where the hidden test pins it, one sentence on the required behaviour (for example "an isolated action is still saved exactly once, after the usual delay"); without it the hidden test would be unfair. The workspace, the visible test command and the hidden test are unchanged.

- **Single answer, 3 runs per task: 36 of 36 fixed**, $0.17 and 0.5 minutes per run ($6.11 in all). No run read the source repositories (checked in all 36 session transcripts), and every workspace had a single commit with no history.
- With no task that a single answer gets wrong, there was nothing for level 0 or a tournament to win, so they were not run.

What makes these bugs easy even without a report: the workspace is a real repository with its tests, the visible test command names the test files of the affected area, and Sonnet reads the code around the symptom, finds the cause and checks the fix against the suite. On this benchmark a careful single answer with tools is as good as any of the multi-answer methods tried, and costs the least.

## 2026-10-26 · version 0.2 smoke run

Crucible 0.2 (level 0 first) on write-02 with Sonnet, headless: the model wrote 8 checks and a script that measured all 8, passed on the first attempt, used no sub-agents, and met every requirement, in 25 seconds for $0.11. A first try without the explicit "always go through `crucible.py`" rule in SKILL.md got the right answer too, but ran its check script by hand and skipped the run record; the rule fixed it.

Earlier pilot (Opus, 4 tasks, single vs Crucible): both arms 4/4; Crucible cost about 9× more ($1.70 against $0.18 per task) and took 4.3 minutes against 0.6.
