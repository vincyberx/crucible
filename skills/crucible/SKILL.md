---
name: crucible
description: Verify first, tournament only if verification fails. Turns a task into explicit acceptance checks (measured by a small script wherever they can be), answers, and fixes the answer until every check passes, with no extra sub-agents. Only if the checks still fail, or the user asks, it runs a small tournament of sub-agents that chase different hypotheses (bug causes, alternative designs), with real tests, one blind judge and a red team on the winner. Use when an answer was not good enough ("that's wrong", "try harder", "make them compete", "/crucible"), when a deliverable has strict requirements (limits, formats, required sections), for a bug whose cause is unclear, or for a design choice with real alternatives. If you start it on your own initiative, ask the user before any tournament.
---

# Crucible

Measured on its own benchmark (`bench/CALIBRATION.md` in the repository): most of what goes wrong in a good model's answer is a requirement it skimmed, and writing the requirements down as checks and verifying against them fixes that for the price of one answer. A tournament costs several times more and has to earn its place, so it comes second.

You are the **host**. The script `crucible.py` (next to this file; call it by its absolute path, written `CRUCIBLE` below) keeps the state, runs the check script and the tests, manages git worktrees, the budget and the blind labels.

**When the user invoked Crucible (typed `/crucible`, named it, or asked for it), run it, even if the task looks simple.** They asked for a verified answer, not just an answer; level 0 costs almost nothing extra.

**Always go through `crucible.py`: `init`, then `check`, then whatever `next` says.** Do not run your check script by hand and do not write the deliverable straight to its final place. The script freezes the checks so they cannot drift to fit the answer, counts the attempts, writes the record, and is the only way to escalate to a tournament. At the end you copy the deliverable from the run folder to wherever the user or the task wants it.

## 1 · Frame the task (no sub-agent calls)

Sub-agents, if any, cannot see this conversation: what is not in these files does not exist for them. Write them in `.crucible/draft/` in the project (or the current directory):

- `task.md`: the task, self-contained. The goal, the context and the constraints from the conversation, the relevant files (repository-relative paths), what to deliver. If the user rejected an earlier answer, say what was wrong with it.
- `checks.md`: 3 to 8 numbered acceptance criteria (`1. ...`), each one checkable by reading or running the result. Go through the task sentence by sentence: every explicit requirement (a limit, a label, a format, a value to use, something to leave out) becomes a check. "Handles an empty input by returning []" is a check; "is high quality" is not.
- `check.py`, **where checks can be measured**: a short standard-library Python script. It receives the path of the answer file as its only argument (for code, it runs inside the candidate's working tree) and prints one JSON object, `{"1": true, "4": false}`, for the checks it can decide: counts, limits, required or forbidden strings, formats, dates, the result of running something. Leave out what a script cannot judge. Never make the script check one particular answer: it must check the requirement.

If a check depends on something only the user knows, ask at most two short questions first. If the user rejected a previous answer of yours, save it as `.crucible/draft/baseline.md`.

For code, decide:

- `--code` when the task changes files in a git repository. The work happens in worktrees; uncommitted edits are included, untracked files are not.
- `--test-cmd "..."`: the command that proves the code works. Find it in the project; do not invent one.
- `--setup-cmd "..."` if a fresh checkout needs something before tests run, for example `ln -s {root}/node_modules node_modules`.

## 2 · Start

```
python3 CRUCIBLE init --task .crucible/draft/task.md --checks .crucible/draft/checks.md \
  [--check-script .crucible/draft/check.py] [--baseline .crucible/draft/baseline.md] \
  [--code --test-cmd "..." --setup-cmd "..."] [--ask]
```

Pass `--ask` if the user did not ask for Crucible: you will then ask before any tournament. To skip level 0 and go straight to a tournament (the user asked for one, or the problem is a design choice with no single right answer), add `--tournament` (or `--deep` for a bigger one) and `--hypotheses <file>`; `python3 CRUCIBLE plan --tournament` prints its cost.

## 3 · Level 0: answer, check, fix

No sub-agents: you do it. The script tells you where to write (`candidates/c0/solution.md`; for code, a private worktree). Then:

```
python3 CRUCIBLE check
```

It runs the tests and the check script. If something measured fails, fix it and run `check` again. If everything measured passes, it lists the checks no script can decide: go through them yourself, one by one, honestly, against your answer. Then `check --self-verified` if they pass, or `check --self-failed 2,5` if some still fail and you cannot fix them. You get three attempts by default.

When every check passes, the run is finished: go to step 5.

## 4 · Level 1: a tournament of hypotheses

If level 0 runs out of attempts, the script stops at `escalate`. If you passed `--ask`, ask the user first, with the cost the script prints. Then write **hypotheses**, one bullet each, for the other candidates:

- for a bug or a failing test: different possible causes ("the cache key ignores the locale", "the retry fires before the lock is released");
- for a design: genuinely different designs;
- for other tasks: different methods, informed by what failed at level 0.

```
python3 CRUCIBLE escalate --hypotheses .crucible/draft/hypotheses.md
```

One candidate repairs your level-0 attempt using its failure report; the others each chase one hypothesis. Your attempt stays in the comparison. From here, do exactly what the script prints until it says `Finished`:

- **Sub-agent jobs**: spawn one sub-agent per job, all of one phase at the same time, each with exactly the prompt the script printed. Wait for every reply, then run the `collect` command it gave you.
- **verify**: run the command it gave you (tests and check script; can be slow).
- After a context compaction, `python3 CRUCIBLE next` says where you are.

Rules: never read the candidates' work during the run; never edit what sub-agents produce or write their output for them; never change the task between phases. If a sub-agent fails, `collect` says so; `next` re-issues the job (one more call) and `collect --partial` goes on without it.

### Spawning a sub-agent on your host

Each job needs an independent sub-agent with a fresh context that can read and write files and, for code, run commands.

- **Claude Code**: the Agent tool, `subagent_type` general-purpose, one call per job, all the jobs of a phase in ONE message. Do not set `isolation`: Crucible makes its own worktrees.
- **Codex**: ask explicitly for one sub-agent per job, run them in parallel and wait for all of them.
- **Other hosts**: use the host's sub-agent or delegation tool. With none, stop at level 0 and tell the user a tournament needs isolated sub-agents: never simulate them in one conversation.

## 5 · Deliver

Read `RESULT.md` in the run folder. If the task says where the deliverable goes (a file, a path), copy `final.md` there now, unchanged. Then tell the user:

- the outcome in one sentence, then the deliverable: `final.md`, or for code what `final.patch` changes;
- whether it stopped at level 0 (and after how many attempts) or needed the tournament; which checks were measured by the script; for a tournament, what the red team found and whether the revision held up;
- any check still failing, plainly;
- if a baseline ranked first, that the user's earlier answer was better.

For code, apply the patch only after the user agrees (`python3 CRUCIBLE apply`), then `python3 CRUCIBLE cleanup`. If the user wants a tournament after a level-0 success, `escalate` still works.

## Limits

- The checks are only as good as you write them. A requirement you did not turn into a check is not verified.
- Checks you verify yourself are weaker than measured ones: write the script wherever a requirement can be counted or run.
- The tournament's own value is not established by the benchmark yet; use it for what level 0 cannot settle.
