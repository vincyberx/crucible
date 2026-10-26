#!/usr/bin/env python3
"""Benchmark: does Crucible beat a single answer from the same model, and at what cost?

Each task runs in a fresh scratch folder, once per arm:
  single     the host answers alone, no sub-agents
  checklist  the host answers alone, but first writes the task's acceptance checks
             and verifies its answer against them (Crucible's framing, no tournament)
  crucible   the host runs the Crucible skill (installed into the scratch project):
             level 0, then a tournament only if its checks fail
  arena      the host runs arena-skill --quick, a 16-agent bracket tournament, for
             comparison (clone github.com/Jakeschincariol/arena-skill into bench/vendor)

Then the result is scored without any model where possible: hidden tests for
code tasks, an exact answer for reasoning tasks. Writing tasks are scored by a
blind rubric check run on the same host (weaker evidence, reported apart).

  python3 bench/run.py --host claude --arms single,crucible
  python3 bench/run.py --host claude --tasks code-01,reason-02 --repeat 3
  python3 bench/run.py --report bench/results/<run>      # rebuild the table

The agents run with shell access inside the scratch folders. Standard library only.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SKILL = REPO / "skills" / "crucible"
ARENA_SKILL = HERE / "vendor" / "arena-skill" / "skills" / "arena"
TASKS = HERE / "tasks"

SINGLE = """{task}

Work on this alone: do not spawn sub-agents and do not ask questions.
"""

CHECKLIST = """{task}

Work on this alone: do not spawn sub-agents and do not ask questions.

Before you write anything, turn the task into a numbered checklist of acceptance checks,
each one checkable by reading the result, and save it to CHECKLIST.md. Then produce the
deliverable. Then check the deliverable against every item of the checklist, one by one,
and fix whatever fails before you finish. CHECKLIST.md is for you; the deliverable goes
where the task says.
"""

ARENA = """Use the arena skill, installed in this project, with --quick on the task below. The
user has already agreed to the cost: do not ask for confirmation and do not ask questions.
When the tournament is finished, write the winning solution to ANSWER.md exactly as the task
requires: the file must contain only the deliverable.

TASK
----
{task}
"""

CRUCIBLE = """Use the crucible skill, installed in this project, on the task below. The user
has already agreed to the cost: do not ask for confirmation and do not ask questions.
{code_hint}When the run is finished, deliver the result where the task asks for it:
{deliver}

TASK
----
{task}
"""

RUBRIC_JUDGE = """You are checking a piece of writing against a rubric. Read the task in
{task}, the rubric in {rubric} and the answer in {answer}. For each numbered
criterion decide pass or fail, strictly, from the text alone. Write {out} as JSON
only: {{"passes": [true, false, ...], "notes": "..."}} with one boolean per criterion,
in order. Then reply DONE."""


def sh(cmd, cwd, timeout=None, shell=False):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                          shell=shell)


def git_init(path):
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.name=bench", "-c", "user.email=bench@localhost",
                  "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "start"]):
        sh(["git"] + args, path)


def host_cmd(host, prompt, cwd, model):
    if host == "claude":
        # --setting-sources project: no user CLAUDE.md, hooks or plugins, so every
        # arm runs in the same plain environment and the user's setup is untouched
        cmd = ["claude", "-p", prompt, "--output-format", "json", "--strict-mcp-config",
               "--setting-sources", "project", "--permission-mode", "acceptEdits",
               "--allowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep", "Agent", "Skill"]
        if model:
            cmd += ["--model", model]
        return cmd
    if host == "codex":
        cmd = ["codex", "exec", "--skip-git-repo-check", "--ephemeral", "-s", "workspace-write",
               "-C", str(cwd), "--json", "-o", str(Path(cwd) / ".bench-last.txt"), prompt]
        if model:
            cmd[2:2] = ["-m", model]
        return cmd
    raise SystemExit("unknown host " + host)


def usage_of(host, stdout):
    """Cost and tokens as reported by the host, best effort."""
    if host == "claude":
        try:
            d = json.loads(stdout)
        except ValueError:
            return {"error": "no JSON from claude"}
        u = d.get("usage") or {}
        return {"cost_usd": d.get("total_cost_usd"), "turns": d.get("num_turns"),
                "is_error": d.get("is_error"), "models": sorted(d.get("modelUsage") or {}),
                "tokens": sum(u.get(k) or 0 for k in ("input_tokens", "output_tokens",
                                                       "cache_creation_input_tokens",
                                                       "cache_read_input_tokens"))}
    # codex --json prints one event per line; keep the last token count it reports
    tokens = None
    for line in stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        u = ev.get("usage") or (ev.get("msg") or {}).get("info", {}).get("total_token_usage")
        if isinstance(u, dict):
            tokens = sum(v for v in u.values() if isinstance(v, int))
    return {"tokens": tokens}


def install_skill(host, ws, name="crucible", src=SKILL):
    dest = ws / (".claude/skills/" if host == "claude" else ".agents/skills/") / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__"))
    exclude = ws / ".git" / "info" / "exclude"
    if exclude.parent.exists():
        exclude.write_text(exclude.read_text() + "\n.claude/\n.agents/\n.crucible/\n.arena/\n")


def prepare(task_dir, meta, ws, arm, host):
    if ws.exists():
        shutil.rmtree(ws)
    if meta["kind"] == "code":
        shutil.copytree(task_dir / "workspace", ws)
    elif meta["kind"] == "repo":
        # the tree as it was before the fix, with no history: `git log` cannot reveal the fix
        ws.mkdir(parents=True)
        archive = subprocess.run(["git", "-C", meta["repo"], "archive", meta["base_commit"]],
                                 capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", str(ws)], input=archive.stdout, check=True)
    else:
        ws.mkdir(parents=True)
    git_init(ws)
    if meta["kind"] == "repo" and meta.get("setup_cmd"):
        sh(meta["setup_cmd"].replace("{repo}", meta["repo"]), ws, timeout=600, shell=True)
        # whatever the setup created (symlinks to dependencies) stays out of the diff
        exclude = ws / ".git" / "info" / "exclude"
        added = sh(["git", "ls-files", "--others", "--exclude-standard"], ws).stdout.split()
        exclude.write_text(exclude.read_text() + "".join("\n/" + p for p in added) + "\n")
    if arm in ("crucible", "tournament"):
        install_skill(host, ws)
    elif arm == "arena":
        # github.com/Jakeschincariol/arena-skill, cloned by hand into bench/vendor
        if not ARENA_SKILL.exists():
            raise SystemExit("arena arm: clone arena-skill into %s first" % ARENA_SKILL.parents[1])
        install_skill(host, ws, "arena", ARENA_SKILL)


def prompt_for(arm, meta, task_text):
    if arm == "single":
        return SINGLE.format(task=task_text)
    if arm == "checklist":
        return CHECKLIST.format(task=task_text)
    if arm == "arena":
        return ARENA.format(task=task_text)
    if meta["kind"] in ("code", "repo"):
        hint = "This is a code task: use --code with --test-cmd \"%s\"" % meta["test_cmd"]
        if meta.get("worktree_setup"):
            hint += " and --setup-cmd \"%s\"" % meta["worktree_setup"]
        hint += ".\n"
        deliver = "apply the final patch to this working tree, then clean up the worktrees."
    else:
        hint = ""
        deliver = "write the final deliverable to ANSWER.md exactly as the task requires."
    if arm == "tournament":
        hint += ("Skip level 0 and start directly with a tournament: write three hypotheses "
                 "(for a bug, three different possible causes) and pass --tournament "
                 "--hypotheses <file> to init.\n")
    return CRUCIBLE.format(code_hint=hint, deliver=deliver, task=task_text)


def crucible_calls(ws):
    calls = None
    for st in ws.glob(".crucible/*/state.json"):
        try:
            calls = (calls or 0) + json.loads(st.read_text())["calls"]
        except (ValueError, KeyError):
            pass
    return calls


def norm(s):
    return re.sub(r"\s+", " ", s.strip().strip(".").lower())


def score(task_dir, meta, ws):
    kind = meta["kind"]
    if kind in ("code", "repo"):
        hidden = task_dir / "hidden"
        if hidden.exists():
            shutil.copytree(hidden, ws, dirs_exist_ok=True)
        shell = kind == "repo"      # repo commands carry paths and flags
        vis = sh(meta["test_cmd"] if shell else meta["test_cmd"].split(), ws, 600, shell)
        hid = sh(meta["hidden_cmd"] if shell else meta["hidden_cmd"].split(), ws, 600, shell)
        (ws / ".bench-hidden.txt").write_text(hid.stdout[-4000:] + hid.stderr[-4000:])
        ok = vis.returncode == 0 and hid.returncode == 0
        return {"score": 1.0 if ok else 0.0, "visible": vis.returncode == 0,
                "hidden": hid.returncode == 0}
    answer = ws / "ANSWER.md"
    if not answer.exists():
        return {"score": 0.0, "error": "no ANSWER.md"}
    if kind == "reason":
        found = re.findall(r"(?m)^\s*ANSWER:\s*(.+?)\s*$", answer.read_text())
        if not found:
            return {"score": 0.0, "error": "no ANSWER: line"}
        got, want = found[-1], meta["answer"]
        if meta.get("answer_type") == "set":
            same = {norm(x) for x in got.split(",")} == {norm(x) for x in want.split(",")}
        elif meta.get("answer_type") == "integer":
            same = re.sub(r"[^\d-]", "", got) == re.sub(r"[^\d-]", "", want)
        else:
            same = norm(got) == norm(want)
        return {"score": 1.0 if same else 0.0, "got": got}
    return {"score": None, "pending": "rubric"}


def scripted_checks(task_dir, answer):
    """{criterion: pass} for the rubric criteria the task's check.py can decide."""
    chk = task_dir / "check.py"
    if not chk.exists():
        return {}
    p = sh([sys.executable, "-I", str(chk), str(answer)], task_dir, timeout=60)
    try:
        return {int(k): bool(v) for k, v in json.loads(p.stdout).items()}
    except ValueError:
        return {}


def judge_writing(host, task_dir, ws, model):
    """Scripted checks where they exist; a blind model judge for the rest."""
    n = len(re.findall(r"(?m)^\s*\d+\.\s", (task_dir / "rubric.md").read_text()))
    scripted = scripted_checks(task_dir, ws / "ANSWER.md")
    llm = None
    if len(scripted) < n:
        res = model_judge(host, task_dir, ws, model)
        if "error" in res:
            return res
        llm = res["rubric"]
        if len(llm) != n:
            return {"score": None, "error": "rubric judge gave %d verdicts for %d criteria"
                    % (len(llm), n)}
    passes = [scripted[i + 1] if (i + 1) in scripted else bool(llm[i]) for i in range(n)]
    return {"score": round(sum(passes) / n, 3), "rubric": passes,
            "scripted": sorted(scripted), "llm_rubric": llm}


def model_judge(host, task_dir, ws, model):
    out = ws / ".bench-rubric.json"
    # the judge must not see which arm wrote it: not even in the folder name
    copy = ws.parent / ("blind-" + hashlib.sha1(ws.name.encode()).hexdigest()[:10])
    if copy.exists():
        shutil.rmtree(copy)
    copy.mkdir()
    shutil.copyfile(ws / "ANSWER.md", copy / "answer.md")
    shutil.copyfile(task_dir / "task.md", copy / "task.md")
    shutil.copyfile(task_dir / "rubric.md", copy / "rubric.md")
    prompt = RUBRIC_JUDGE.format(task=copy / "task.md", rubric=copy / "rubric.md",
                                 answer=copy / "answer.md", out=copy / "verdict.json")
    sh(host_cmd(host, prompt, copy, model), copy, timeout=900)
    try:
        passes = json.loads((copy / "verdict.json").read_text())["passes"]
        shutil.copyfile(copy / "verdict.json", out)
        return {"rubric": passes}
    except (OSError, ValueError, KeyError) as e:
        return {"score": None, "error": "rubric judge failed: %s" % e}


def rescore(out_dir):
    path = out_dir / "results.json"
    rows = json.loads(path.read_text())
    for r in rows:
        if r["kind"] != "write" or not (r.get("llm_rubric") or r.get("rubric")):
            continue
        task_dir = TASKS / r["task"]
        ws = out_dir / "work" / ("%s-%s-%d" % (r["task"], r["arm"], r["rep"]))
        llm = r.get("llm_rubric") or r["rubric"]
        scripted = scripted_checks(task_dir, ws / "ANSWER.md")
        passes = [scripted[i + 1] if (i + 1) in scripted else bool(x) for i, x in enumerate(llm)]
        r.update(score=round(sum(passes) / len(passes), 3), rubric=passes,
                 scripted=sorted(scripted), llm_rubric=llm)
    path.write_text(json.dumps(rows, indent=2))


def report(out_dir):
    rows = json.loads((out_dir / "results.json").read_text())
    arms = sorted({r["arm"] for r in rows})
    lines = ["# Crucible benchmark", "", "| task | kind | " + " | ".join(arms) + " |",
             "|---|---|" + "---|" * len(arms)]
    by_task = {}
    for r in rows:
        by_task.setdefault((r["task"], r["kind"]), {}).setdefault(r["arm"], []).append(r)
    for (task, kind), per_arm in sorted(by_task.items()):
        cells = []
        for arm in arms:
            rs = per_arm.get(arm, [])
            sc = [r["score"] for r in rs if r.get("score") is not None]
            cost = [r.get("cost_usd") or 0 for r in rs]
            cell = "%.2f" % (sum(sc) / len(sc)) if sc else "–"
            if any(cost):
                cell += " · $%.2f" % (sum(cost) / len(cost))
            calls = [r.get("calls") for r in rs if r.get("calls")]
            if calls:
                cell += " · %d calls" % round(sum(calls) / len(calls))
            cells.append(cell)
        lines.append("| %s | %s | %s |" % (task, kind, " | ".join(cells)))
    lines += ["", "## Totals", "", "| arm | kind | mean score | mean cost | mean minutes |",
              "|---|---|---|---|---|"]
    for arm in arms:
        for kind in ("code", "repo", "reason", "write"):
            rs = [r for r in rows if r["arm"] == arm and r["kind"] == kind]
            sc = [r["score"] for r in rs if r.get("score") is not None]
            if not rs:
                continue
            cost = [r.get("cost_usd") or 0 for r in rs]
            mins = [r.get("seconds", 0) / 60 for r in rs]
            lines.append("| %s | %s | %s | $%.2f | %.1f |" % (
                arm, kind, "%.2f" % (sum(sc) / len(sc)) if sc else "–",
                sum(cost) / len(cost), sum(mins) / len(mins)))
    lines += ["", "Code, real bugs and reasoning are scored without a model (hidden tests, exact answers). "
              "Writing is scored by a blind rubric check on the same host: weaker evidence."]
    (out_dir / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--host", default="claude", choices=["claude", "codex"])
    p.add_argument("--arms", default="single,crucible")
    p.add_argument("--tasks", help="comma-separated ids or prefixes (default: all)")
    p.add_argument("--tasks-dir", help="folder of tasks (default: bench/tasks); real-bug "
                   "tasks built from private repositories live in bench/private-tasks")
    p.add_argument("--repeat", type=int, default=1)
    p.add_argument("--jobs", type=int, default=1, help="agent runs at the same time")
    p.add_argument("--model")
    p.add_argument("--timeout", type=int, default=3600, help="seconds per agent run")
    p.add_argument("--out", help="results folder (default: bench/results/<timestamp>)")
    p.add_argument("--report", help="only rebuild RESULTS.md for this results folder")
    p.add_argument("--rescore", help="re-apply the scripted checks to a results folder, "
                   "keeping the model judge's verdicts for the other criteria")
    p.add_argument("--dry-run", action="store_true", help="print the plan, run nothing")
    a = p.parse_args()
    global TASKS
    if a.tasks_dir:
        TASKS = Path(a.tasks_dir).resolve()

    if a.report:
        report(Path(a.report))
        return
    if a.rescore:
        rescore(Path(a.rescore).resolve())
        report(Path(a.rescore))
        return

    tasks = sorted(d for d in TASKS.iterdir() if (d / "meta.json").exists())
    if a.tasks:
        wanted = a.tasks.split(",")
        tasks = [d for d in tasks if any(d.name.startswith(w) for w in wanted)]
    arms = a.arms.split(",")
    out_dir = Path(a.out or HERE / "results" / time.strftime("%Y%m%d-%H%M%S")).resolve()
    print("%d task(s) × %s × %d repeat(s) on %s → %s" % (len(tasks), arms, a.repeat, a.host, out_dir))
    if a.dry_run:
        for d in tasks:
            print("  " + d.name)
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    results_file = out_dir / "results.json"
    rows = json.loads(results_file.read_text()) if results_file.exists() else []
    done = {(r["task"], r["arm"], r["rep"]) for r in rows}
    lock = threading.Lock()

    def run_one(item):
        d, rep, arm = item
        meta = json.loads((d / "meta.json").read_text())
        ws = out_dir / "work" / ("%s-%s-%d" % (meta["id"], arm, rep))
        prepare(d, meta, ws, arm, a.host)
        prompt = prompt_for(arm, meta, (d / "task.md").read_text())
        t0 = time.time()
        try:
            proc = sh(host_cmd(a.host, prompt, ws, a.model), ws, timeout=a.timeout)
            stdout, rc = proc.stdout, proc.returncode
        except subprocess.TimeoutExpired:
            stdout, rc = "", "timeout"
        row = {"task": meta["id"], "kind": meta["kind"], "arm": arm, "rep": rep,
               "host": a.host, "exit": rc, "seconds": round(time.time() - t0)}
        row.update(usage_of(a.host, stdout))
        row["calls"] = crucible_calls(ws)
        (ws / ".bench-host-output.txt").write_text(stdout)
        row.update(score(d, meta, ws))
        if meta["kind"] == "write" and row.get("pending"):
            row.update(judge_writing(a.host, d, ws, a.model))
            row.pop("pending", None)
        with lock:
            rows.append(row)
            results_file.write_text(json.dumps(rows, indent=2))
            print("%-10s %-9s rep %d  score %s  %ss  %s" % (
                meta["id"], arm, rep, row.get("score"), row["seconds"],
                "$%.2f" % row["cost_usd"] if row.get("cost_usd") else ""), flush=True)

    todo = [(d, rep, arm) for d in tasks for rep in range(a.repeat) for arm in arms
            if (json.loads((d / "meta.json").read_text())["id"], arm, rep) not in done]
    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        list(pool.map(run_one, todo))
    report(out_dir)


if __name__ == "__main__":
    sys.exit(main())
