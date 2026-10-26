# Crucible — design

## What the benchmark taught us

Version 0.1 was a lean tournament: three candidates with task-specific approaches, tests run in worktrees, one blind checklist judge, a red team on the winner. It cost 5–10 sub-agent calls instead of the ~91–595 of bracket tournaments, and it worked. Then the benchmark ([bench/CALIBRATION.md](bench/CALIBRATION.md)) asked where the gain came from:

- On a writing task with strict requirements, a single answer met all of them 3 times in 10; the tournament 10 in 10. But a single answer that wrote its own checklist and verified against it reached 9 in 10, at the cost of a single answer. No candidate in the tournament made the single answer's mistake: the explicit checks did the work, not the competition.
- On code and reasoning tasks built with deliberate traps (greedy-versus-optimal, re-applied tiebreaks, operator semantics, rule-ordering), a single Sonnet answer with tools was right 23 times in 24. No tournament can improve on that.
- A 16-agent bracket tournament reached the same outcome as both, at 14× the cost of Crucible v0.1.

So version 0.2 puts verification first and keeps the tournament for what verification cannot settle.

## The principle

Spend effort where it changes the outcome, and measure instead of judging wherever possible.

1. **Write the requirements down as checks.** Most failures of a strong model are requirements it skimmed. Every explicit requirement of the task becomes a numbered check.
2. **Measure what can be measured.** The host writes a small check script for the checks that can be counted or run. A script does not skim; in the benchmark it agreed with a model judge everywhere the judge was right, and caught the cases where the judge's reading was wrong.
3. **Fix until the checks pass, without sub-agents.** That is level 0, and it costs about one answer.
4. **Escalate only on failure, and escalate with hypotheses.** If level 0 keeps failing, or the user asks, a small tournament explores different explanations of why, or different designs, starting from the failed attempt.
5. **Never regress, never exceed the budget.** A revision that fails a test or a check the original passed is discarded; the call cap is checked before every sub-agent call.

## Level 0

```
frame (host): task.md · checks.md · check.py (measurable checks) · [baseline.md]
      │
answer (host) ── text: candidates/c0/solution.md · code: a private worktree
      │
check ── tests + frozen check script → measured failures count as a failed attempt
      │       └─ all measured checks pass → host verifies the unmeasured ones itself
      │
      ├─ all pass ──────────────────────────────────────────► deliver
      ├─ fail, attempts left ─► fix (feedback.md lists what failed) ─► check
      ▼
escalate ── ask the user first if Crucible was not requested ─► level 1, or finish
```

- **The check script** receives the answer file (and runs inside the worktree for code) and prints `{"<check>": true|false}` for the checks it decides. `init` copies it into the run folder: from then on nobody can edit the checks to make an answer pass.
- **Unmeasured checks** are verified by the host itself, after every measured check passes, and reported with `--self-verified` or `--self-failed N,N`. This is weaker evidence, and the result says which checks were measured and which were self-verified.
- **Attempts**: three by default (`--max-fixes 2`). A measured failure counts immediately; the host cannot loop on a failing check without spending an attempt.

## Level 1

```
escalate --hypotheses H
      │
candidates (parallel): c1 repairs c0 from its feedback · c2..ck each chase one hypothesis
      │                 c0 itself stays in the comparison
verify ── tests + check script on every candidate (0 calls)
      │
judge ×1 ── blind, all candidates, check by check; scripted results are facts
      │
      ├─ not clean, budget left ─► second wave: 1 repair + 1 fresh ─► verify ─► judge
      ▼
red team ×1 ── attack the winner, prove it (failing tests for code)
      │
      ├─ no FATAL/MAJOR finding and no failing test ──────────► deliver
      ▼
revise ×1 ── concede and fix, or rebut; adopt strengths of the losers
      │
check ── tests and check script must not regress (0 calls) · otherwise a blind final judge
      │
final ×1 (with a baseline, or when nothing can be measured) ── blind comparison
      │
deliver ── RESULT.md · final.md or final.patch
```

**Hypotheses** replace v0.1's "approaches". For a bug they are candidate causes; each candidate tests its hypothesis first and, if the evidence refutes it, says so and solves the task from what the evidence shows. For a design they are genuinely different designs. The level-0 failure report is given to every candidate, so nobody repeats the first mistake.

**Starting directly at level 1** (`--tournament`, or `--deep` for five candidates) is for when the user asks for it or the task has no single right answer.

### Decision rules (in `crucible.py`, not left to a model)

Candidates are ordered by, in this order: tests pass, the check script ran, no fatal flaw, checks passed (the script's measurement where it exists, the judge's verdict elsewhere), the judge's rank. The judge's taste breaks ties; it never overrides a measurement.

The leader is **clean** when every check passes, nothing is fatal and the tests pass.

| after the judge | budget | next |
|---|---|---|
| not clean | room for a wave + red team + revision | second wave: one *repair* of the leader with the feedback, one *fresh* attempt with the lessons |
| clean | room for the red team | red team |
| not clean | room for red team + revision | red team |
| otherwise | – | deliver the leader |

The red team always runs when the budget allows, even on consensus: candidates from one model share blind spots, and agreement is where they hide. The revision runs only if the attack finds something real.

### Budget

| path | sub-agent calls |
|---|---|
| level 0 | 0 |
| level 1, the red team finds nothing | k + 2 (5 with three candidates) |
| level 1, typical | 6–7 |
| level 1, with a second wave | 9–10 |
| `--deep` | up to 15–20 |

The default cap is 12 (20 with `--deep`).

## Blindness

The judge never sees hypotheses, candidate ids or revealing paths: every solution is copied under a neutral folder (`judge/r1/A/`), and labels are shuffled with a seeded generator. Notes written for the judge live in a separate file from the answer, so the delivered file contains only the deliverable. The final comparison against a baseline is blind too, and the result says plainly when the user's original answer was better.

## Safety

- Work happens in git worktrees under `.crucible/<run>/wt/`, created from `git stash create`: uncommitted edits are included without touching the user's branch, index or stash list. Untracked files are not, and the run says so.
- `.crucible/` goes in `.git/info/exclude`, never in the user's `.gitignore`.
- The script warns if the main working tree changed during the run, and `apply` refuses to apply the patch if it did.
- Every run has a random token stored outside the project (in the user's cache folder). A `.crucible/` folder that came with a cloned repository has no token, so its commands are never run. Runs are looked up only in the current folder and the repository root.
- The check script runs with `python3 -I`, from a frozen copy.

## Portability

Everything that decides the outcome is plain files and standard-library Python. Only *how to start an isolated sub-agent* depends on the host, and `SKILL.md` covers it in a few lines per host. Level 0 needs no sub-agents at all, so it works on any host that can run Python.

| host | skills folder | sub-agents | status |
|---|---|---|---|
| Claude Code | `.claude/skills/` | Agent tool, parallel | primary target, tested |
| Codex | `.agents/skills/` | built-in, spawned when asked | to be tested |
| Gemini CLI | `.gemini/skills/` | in preview | untested |

## Context hygiene

During a tournament the host never reads the candidates' work: every sub-agent writes files and replies with one line. The state lives in `state.json`; after a context compaction, `crucible.py next` says exactly what to do.

## Open questions

- **Does the tournament beat level 0 anywhere?** Not shown yet. Twelve real bugs from git history (the tree before the fix, the fix's own test as the hidden test) were all fixed by a single Sonnet answer, both with a full report (24 of 24) and with a symptom-only report (36 of 36), so no tournament had room to win. The remaining candidates are tasks a benchmark struggles to score: open-ended design, problems spread over a large codebase, bugs that need a live system to reproduce.
- **Is a cheap model plus Crucible as good as a strong model alone?** Worth measuring once the first question has an answer.

## Known limits

- A requirement that never became a check is not verified. The checks are only as good as the host writes them.
- Self-verified checks are weaker than measured ones.
- The judge and the red team are models; checks and tests limit how much their taste decides.
- A vague task gives a vague answer at any level.
