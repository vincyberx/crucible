# Crucible

**Verify first. Run a tournament only when verification fails.**

When your coding agent's answer is not good enough, the usual fix is to ask again, or to throw many agents at it. Crucible does what its own benchmark says works best, in order:

1. **Level 0, no sub-agents.** Your agent turns the task into explicit acceptance checks, writes a small script that measures every check that can be measured (word limits, required labels, formats, values, a command that must pass), answers, and fixes the answer until every check passes. It costs about as much as one ordinary answer.
2. **Level 1, only if level 0 still fails** (or you ask for it). A small tournament of sub-agents: one repairs the failed attempt from its failure report, the others chase different **hypotheses**, such as different causes of a bug or different designs. Tests and the check script rank them first, a blind judge decides the rest, a red team attacks the winner, and a revision is thrown away if it does not hold up. 5 to 10 sub-agent calls, with a hard cap.

It never edits your project during a run. Code comes back as a patch, and your agent asks before applying it.

## Why this order

Measured with Claude Sonnet 5.5 on a writing task with strict requirements, 10 runs per arm ([bench/CALIBRATION.md](bench/CALIBRATION.md)):

| | all requirements met | cost per run |
|---|---|---|
| a single answer | 3 of 10 | $0.07 |
| one answer that writes its checklist and verifies against it | 9 of 10 | $0.08 |
| Crucible v0.1 tournament (5 sub-agent calls) | 10 of 10 | $0.50 |
| [arena-skill](https://github.com/Jakeschincariol/arena-skill) `--quick` (91 calls), 3 runs | 3 of 3 | $7.16 |

Most of the gain came from writing the requirements down and checking them, not from the tournament. On the harder code and reasoning tasks of the benchmark, a single Sonnet answer was already right 23 times out of 24. On twelve real bugs taken from the git history of the author's repositories, it fixed every one: 24 of 24 with a full bug report, and 36 of 36 with a report that gives only the symptom. No tournament could show a gain on any of them. That is why level 0 is the default, the checks are measured by a script wherever possible, and the tournament is kept for what level 0 cannot settle: answers that keep failing their checks, problems that need several different ideas tried, design choices with real alternatives. Whether it beats level 0 on those is still unmeasured.

## Cost

| | sub-agent calls |
|---|---|
| Level 0 | 0 (your agent answers and checks itself) |
| Level 1, typical | 6–7 |
| Level 1, with a second wave | 9–10 |
| Level 1 `--deep` (5 candidates) | ≤ 15–20, capped |
| bracket tournament, 16 agents | ~91 |

`crucible.py plan` prints the numbers before anything runs. The token cost of a call depends on your host: every sub-agent starts with the host's own system prompt and tools.

## Install

Crucible is an [Agent Skill](https://agentskills.io): one folder with a `SKILL.md`, the sub-agent briefs and a standard-library Python script. Python 3.9+ and git are the only requirements.

**Claude Code**, as a plugin:

```
/plugin marketplace add vincyberx/crucible
/plugin install crucible@crucible
```

or copy the folder:

```bash
git clone https://github.com/vincyberx/crucible.git
cp -r crucible/skills/crucible ~/.claude/skills/
```

**Codex**: copy `skills/crucible` into `~/.agents/skills/` (or `.agents/skills/` in a repository).

**Gemini CLI**: copy it into `~/.gemini/skills/`. Untested so far; reports welcome.

Level 0 works on any host. Level 1 needs a host that can start sub-agents; without one, Crucible stops at level 0 rather than fake a tournament.

## Use

```
/crucible
/crucible the release notes must stay under 140 words and drop reverted changes
/crucible --tournament the checkout test fails intermittently on CI
```

On its own, `/crucible` takes your last request as the task and the answer you did not like as the one to beat. Your agent can also suggest it when you say something like "that's not right, try again"; then it asks before any tournament.

In Claude Code, accept-edits mode (Shift+Tab) avoids a permission prompt for every file a sub-agent writes under `.crucible/`.

## How it works

The host agent frames the task, writes the checks and the check script, and does level 0 itself. `skills/crucible/crucible.py` keeps the state, freezes and runs the check script, runs the tests, manages the git worktrees, the budget and the blind labels, so a run survives context compaction (`crucible.py next` always says what to do). The sub-agents' exact instructions are in `skills/crucible/briefs/`. The reasoning, decision rules and budget math are in [DESIGN.md](DESIGN.md); the measurements in [bench/CALIBRATION.md](bench/CALIBRATION.md).

## Status

Version 0.2. The state machine is covered by tests (`python3 -m unittest discover -s tests`). The level-0 approach is backed by the benchmark above; the level-1 tournament works end to end with real sub-agents, but its advantage over level 0 has not been measured on a task where it could show one: none of the benchmark's tasks, real bugs included, defeats a single Sonnet answer often enough.

## Credits

Inspired by bracket-style agent tournaments such as [arena-skill](https://github.com/Jakeschincariol/arena-skill), which showed how much a fair, file-based tournament can do inside a coding agent, and which this repository benchmarks against.

## License

MIT
