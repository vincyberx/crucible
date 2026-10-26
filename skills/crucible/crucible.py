#!/usr/bin/env python3
"""Crucible: verify first, run a tournament only when verification fails.

Level 0: the host writes explicit acceptance checks (scripted where they can
be), answers, and fixes its answer until the checks pass. No sub-agents.
Level 1: if the checks still fail, or the user asks for it, a small tournament
of sub-agents chases different hypotheses, starting from the failed attempt.

The host agent (Claude Code, Codex, ...) does the thinking and spawns the
sub-agents. This script does what a model is bad at: randomness, bookkeeping,
budgets, git worktrees, running tests and check scripts. Every run lives in one
JSON file, so a run survives context compaction: `next` always says what to do.

Standard library only. Python 3.9+.
"""

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import NoReturn

VERSION = 1
HERE = Path(__file__).resolve().parent
BRIEFS = HERE / "briefs"

MODES = {
    # candidates in wave 1, extra waves allowed, candidates per extra wave, call cap
    "lite": {"k": 3, "escalations": 1, "wave2": 2, "max_calls": 12},
    "deep": {"k": 5, "escalations": 2, "wave2": 2, "max_calls": 20},
}

LLM_PHASES = ("candidates", "judge", "redteam", "revise", "final")
HOST_PHASES = ("draft", "escalate")
GIT_ID = ["-c", "user.name=crucible", "-c", "user.email=crucible@localhost",
          "-c", "commit.gpgsign=false"]


class CrucibleError(Exception):
    pass


# ---------------------------------------------------------------- utilities

def die(msg) -> NoReturn:
    raise CrucibleError(msg)


def sh(cmd, cwd=None, check=True, timeout=None):
    """Run a command (list) and return stdout. Raises CrucibleError on failure."""
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        die("command failed: %s\n%s" % (" ".join(cmd), (p.stderr or p.stdout).strip()))
    return p.stdout.strip()


def git(args, cwd, check=True):
    return sh(["git"] + GIT_ID + args, cwd=cwd, check=check)


def read(path):
    return Path(path).read_text(encoding="utf-8")


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def numbered_items(text):
    """Items of a numbered list ("1. foo" or "1) foo")."""
    return [m.group(1).strip() for m in re.finditer(r"(?m)^\s*\d+[.)]\s+(\S.*)$", text)]


def list_items(text):
    """Items of a bulleted or numbered list. Continuation lines are joined."""
    items = []
    for line in text.splitlines():
        m = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(\S.*)$", line)
        if m:
            items.append(m.group(1).strip())
        elif items and line.strip() and line.startswith((" ", "\t")):
            items[-1] += " " + line.strip()
    return items


def render(template, values):
    """Tiny mustache: {{VAR}}, {{#VAR}}...{{/VAR}} if truthy, {{^VAR}}...{{/VAR}} if falsy."""
    def block(m):
        kind, name, body = m.group(1), m.group(2), m.group(3)
        truthy = bool(values.get(name))
        return body if (truthy if kind == "#" else not truthy) else ""
    prev = None
    while prev != template:
        prev = template
        template = re.sub(r"\{\{([#^])(\w+)\}\}(.*?)\{\{/\2\}\}", block, template, flags=re.S)

    def var(m):
        name = m.group(1)
        if name not in values:
            die("brief placeholder without a value: " + name)
        return str(values[name])
    return re.sub(r"\{\{(\w+)\}\}", var, template)


def estimate(k, escalations, wave2, code, has_tests, baseline):
    """Sub-agent calls for the fastest, typical and worst path."""
    b = 1 if baseline else 0
    # after a revision, a judge must confirm it did not regress, unless tests can
    final_after_rev = 1 if (not code or not has_tests or baseline) else 0
    fastest = k + 1 + 1 + b          # the red team finds nothing: no revision
    typical = k + 1 + 2 + final_after_rev
    worst = typical + escalations * (wave2 + 1)
    return {"fastest": fastest, "typical": typical, "worst": worst}


# ---------------------------------------------------------------- run storage

def find_run(arg):
    if arg:
        d = Path(arg).resolve()
        if not (d / "state.json").exists():
            die("no Crucible run at " + str(d))
        return d
    here = Path.cwd().resolve()
    # only here and the repository root: never a parent folder we know nothing about
    for d in dict.fromkeys([here, Path(git_root(here) or here)]):
        latest = d / ".crucible" / "latest"
        if latest.exists():
            name = read(latest).strip()
            if not re.fullmatch(r"[\w-]+", name):
                die("refusing %s: it does not name a run" % latest)
            run = d / ".crucible" / name
            if (run / "state.json").exists():
                return run
    die("no Crucible run found here. Start one with: crucible.py init ...")


def token_file(run_id):
    """Proof, kept outside the project, that this machine's user started the run.

    A run's state holds shell commands (the test and setup commands). A state
    file that arrived with a cloned repository or an archive must never get
    them executed, so every command checks the token first.
    """
    base = os.environ.get("CRUCIBLE_HOME") or os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.join(Path.home(), ".cache"), "crucible")
    return Path(base) / "runs" / (run_id + ".token")


def load(run_dir):
    run_dir = Path(run_dir).resolve()
    st = json.loads(read(run_dir / "state.json"))
    tf = token_file(str(st.get("id", "")))
    if (not re.fullmatch(r"[\w-]+", str(st.get("id", ""))) or not tf.exists()
            or read(tf).strip() != st.get("token") or Path(st["dir"]).resolve() != run_dir):
        die("refusing %s: this run was not started by crucible.py for this user on this "
            "machine, so its commands will not be run" % run_dir)
    return st


def save(st):
    path = Path(st["dir"]) / "state.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def log(st, msg):
    st["log"].append(time.strftime("%H:%M:%S ") + msg)


def me():
    return "python3 %s" % HERE.joinpath("crucible.py")


def cmd(st, sub):
    return "%s %s --run %s" % (me(), sub, st["dir"])


# ---------------------------------------------------------------- git / worktrees

def git_root(path):
    try:
        return sh(["git", "rev-parse", "--show-toplevel"], cwd=path)
    except (CrucibleError, FileNotFoundError):
        return None


def main_tree_status(st):
    return git(["status", "--porcelain"], st["root"], check=False)


def exclude_crucible(root):
    common = Path(sh(["git", "rev-parse", "--git-common-dir"], cwd=root))
    if not common.is_absolute():
        common = Path(root) / common
    excl = common / "info" / "exclude"
    excl.parent.mkdir(parents=True, exist_ok=True)
    text = excl.read_text() if excl.exists() else ""
    if ".crucible/" not in text.split():
        excl.write_text(text + ("" if text.endswith("\n") or not text else "\n") + ".crucible/\n")


def add_worktree(st, cid, commit):
    wt = Path(st["dir"]) / "wt" / cid
    git(["worktree", "add", "--detach", "-q", str(wt), commit], st["root"])
    if st.get("setup_cmd"):
        p = subprocess.run(st["setup_cmd"].replace("{root}", st["root"]), shell=True,
                           cwd=wt, capture_output=True, text=True, env=no_bytecode_env())
        if p.returncode != 0:
            log(st, "setup-cmd failed in %s: %s" % (cid, (p.stderr or p.stdout)[-300:]))
    return str(wt)


def snapshot(st, wt, msg):
    git(["add", "-A"], wt)
    git(["commit", "-q", "--no-verify", "--allow-empty", "-m", msg], wt)
    return git(["rev-parse", "HEAD"], wt)


def write_patch(st, wt, commit, dest):
    patch = git(["diff", "--binary", st["base"], commit], wt)
    write(dest, patch + ("\n" if patch else ""))
    return git(["diff", "--stat", st["base"], commit], wt)


def no_bytecode_env():
    # Python's bytecode cache is keyed on mtime in whole seconds and size: a fix
    # of the same length saved within a second of the last run would run stale code
    return dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def run_tests(st, wt, dest):
    if not st.get("test_cmd"):
        return None
    t0 = time.time()
    # shell=True on purpose: the test command is written by the person running
    # Crucible (e.g. "npm test && npm run lint"), like a Makefile target
    try:
        p = subprocess.run(st["test_cmd"], shell=True, cwd=wt, capture_output=True,
                           text=True, timeout=st["test_timeout"], env=no_bytecode_env())
        code, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        code, out = 124, "TIMEOUT after %ss\n%s" % (st["test_timeout"], e.stdout or "")
    tail = "\n".join(out.splitlines()[-80:])
    write(dest, "$ %s\nexit %d (%.0fs)\n\n%s\n" % (st["test_cmd"], code, time.time() - t0, tail))
    return {"exit": code, "passed": code == 0, "log": str(dest)}


def run_checks(st, c, dest, answer=None):
    """Run the frozen check script on a candidate's answer.

    The script gets the answer file as its argument (for code, it runs inside
    the candidate's worktree) and prints a JSON object {"<check number>": bool}
    for the checks it can decide. The others are left to a model."""
    if not st.get("check_script"):
        return None
    answer = Path(answer or Path(c["dir"]) / "solution.md")
    try:
        # -I ignores PYTHON* variables, so -B keeps the bytecode cache off here
        p = subprocess.run([sys.executable, "-I", "-B", st["check_script"], str(answer)],
                           cwd=c["wt"] or st["dir"], capture_output=True, text=True, timeout=300)
        out, err = p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired:
        out, err = "", "check script timed out"
    results = None
    for line in reversed(out.strip().splitlines()):
        if line.strip().startswith("{"):
            try:
                raw = json.loads(line)
                results = {str(int(k)): bool(v) for k, v in raw.items()
                           if 1 <= int(k) <= st["checks_count"]}
                break
            except (ValueError, TypeError, AttributeError):
                pass
    error = None if results is not None else (
        "the check script printed no JSON result: " + (err or out).strip()[-300:])
    write(dest, "%s\n\nstdout:\n%s\nstderr:\n%s\n" % (
        json.dumps(results) if results is not None else error, out[-2000:], err[-2000:]))
    return {"results": results or {}, "error": error, "log": str(dest)}


def failed_scripted(chk):
    return sorted((int(k) for k, v in ((chk or {}).get("results") or {}).items() if not v))


def worse_checks(before, after):
    """True if the scripted checks of `after` fail somewhere `before` passed."""
    if not before or not after:
        return False
    if after.get("error") and not before.get("error"):
        return True
    b, a = before.get("results") or {}, after.get("results") or {}
    return any(b.get(k) and not a.get(k, False) for k in b)


# ---------------------------------------------------------------- init / plan

def cmd_plan(a):
    m = dict(MODES["deep" if a.deep else "lite"])
    if a.candidates:
        m["k"] = a.candidates
    cap = a.max_calls or m["max_calls"]
    e = estimate(m["k"], m["escalations"], m["wave2"], a.code, bool(a.test_cmd) or not a.code,
                 a.baseline)
    if not (a.deep or a.tournament):
        print("Crucible plan: level 0 first, no sub-agents: you answer, the checks run, "
              "you fix what fails (up to %d fixes)." % a.max_fixes)
        print("Only if the checks still fail, level 1:")
    print("  tournament (%s): %d candidates, up to %d extra wave(s) of %d"
          % ("deep" if a.deep else "lite", m["k"], m["escalations"], m["wave2"]))
    print("  sub-agent calls: fastest %d · typical %d · worst %d · hard cap %d"
          % (e["fastest"], e["typical"], min(e["worst"], cap), cap))
    print("  (for scale: a 16-agent bracket tournament needs ~91 calls, 100 agents ~595)")


def cmd_init(a):
    mode = "deep" if a.deep else "lite"
    tournament = bool(a.deep or a.tournament)
    m = dict(MODES[mode])
    if a.candidates:
        if not 2 <= a.candidates <= 8:
            die("--candidates must be between 2 and 8")
        m["k"] = a.candidates
    cap = a.max_calls or m["max_calls"]
    if cap < m["k"] + 1:
        die("--max-calls %d cannot even pay for %d candidates and one judge" % (cap, m["k"]))

    task, checks_text = read(a.task), read(a.checks)
    checks = numbered_items(checks_text)
    if not checks:
        die("checks file has no numbered items. Write them as '1. ...', '2. ...'")
    approaches = list_items(read(a.hypotheses)) if a.hypotheses else []
    if tournament and len(approaches) < m["k"]:
        die("a tournament needs %d hypotheses, found %d%s" % (
            m["k"], len(approaches), " in " + a.hypotheses if a.hypotheses else ""))
    if not task.strip():
        die("task file is empty")
    if a.check_script and not Path(a.check_script).is_file():
        die("no check script at %s" % a.check_script)

    root = Path(a.root or os.getcwd()).resolve()
    base = None
    if a.code:
        r = git_root(root)
        if not r:
            die("--code needs a git repository (no repo at %s)" % root)
        root = Path(r)
        if not git(["rev-parse", "--verify", "-q", "HEAD"], root, check=False):
            die("--code needs at least one commit in the repository")
        # a commit of the working tree as it is now, uncommitted edits included,
        # without touching the user's branch, index or stash list
        base = git(["stash", "create"], root, check=False) or git(["rev-parse", "HEAD"], root)
    if git_root(root):
        # keep run files out of the user's `git status`, without editing .gitignore
        exclude_crucible(git_root(root))

    seed = a.seed if a.seed is not None else random.randrange(1, 10**6)
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-%04d" % random.randrange(10**4)
    d = root / ".crucible" / run_id
    d.mkdir(parents=True)
    write(d / "task.md", task)
    write(d / "checks.md", checks_text)
    if a.hypotheses:
        write(d / "hypotheses.md", read(a.hypotheses))
    if a.baseline:
        write(d / "baseline.md", read(a.baseline))
    check_script = None
    if a.check_script:
        # frozen copy: nobody edits the checks to make an answer pass
        check_script = str(d / "check.py")
        shutil.copyfile(a.check_script, check_script)

    st = {
        "version": VERSION, "id": run_id, "root": str(root), "dir": str(d),
        "mode": mode, "code": bool(a.code), "test_cmd": a.test_cmd, "setup_cmd": a.setup_cmd,
        "test_timeout": a.test_timeout, "base": base, "seed": seed,
        "check_script": check_script, "level": 1 if tournament else 0,
        "max_fixes": a.max_fixes, "fixes_used": 0, "attempts": [], "ask": bool(a.ask),
        "max_calls": cap, "calls": 0, "k": m["k"], "wave2": m["wave2"],
        "escalations_left": m["escalations"], "checks_count": len(checks),
        "has_baseline": bool(a.baseline), "wave": 1, "round": 0,
        "phase": "candidates" if tournament else "draft", "candidates": {}, "pool": [],
        "jobs": {}, "labels": {}, "verdicts": [], "leader": None, "winner": None,
        "redteam": None, "revision": None, "final": None, "outcome": None,
        "untracked_warning": None, "main_status": None, "log": [],
        "token": "%032x" % random.SystemRandom().getrandbits(128),
    }
    write(token_file(run_id), st["token"] + "\n")
    if a.code:
        untracked = git(["ls-files", "--others", "--exclude-standard"], root, check=False)
        if untracked:
            st["untracked_warning"] = "untracked files are not copied into candidate worktrees"
        st["main_status"] = main_tree_status(st)
    if tournament:
        for i in range(m["k"]):
            new_candidate(st, approaches[i], "fresh")
        st["pool"] = list(st["candidates"])
        log(st, "init: level 1 (%s), %d candidates, cap %d calls, seed %d"
            % (mode, m["k"], cap, seed))
    else:
        st["wave"] = 0
        new_candidate(st, "The host's own answer, checked and fixed until the checks pass.",
                      "draft", cid="c0")
        st["wave"] = 1
        log(st, "init: level 0, up to %d fixes, then a %s tournament if the checks still fail"
            % (a.max_fixes, mode))
    save(st)
    write(root / ".crucible" / "latest", run_id + "\n")

    print("Crucible run %s created at %s" % (run_id, d))
    if tournament:
        e = estimate(m["k"], m["escalations"], m["wave2"], st["code"],
                     bool(st["test_cmd"]) or not st["code"], st["has_baseline"])
        print("Budget: typical %d sub-agent calls, hard cap %d." % (e["typical"], cap))
    if st["untracked_warning"]:
        print("WARNING: " + st["untracked_warning"])
    print()
    show_next(st)


def new_candidate(st, approach, kind, parent=None, cid=None, feedback=None, lessons=None):
    cid = cid or "c%d" % (len([k for k in st["candidates"] if k != "c0"]) + 1)
    c = {"wave": st["wave"], "approach": approach, "kind": kind, "parent": parent,
         "dir": str(Path(st["dir"]) / "candidates" / cid), "wt": None,
         "commit": None, "tests": None, "checks": None, "stat": None,
         "feedback": feedback, "lessons": lessons}
    Path(c["dir"]).mkdir(parents=True, exist_ok=True)
    if st["code"]:
        start = st["candidates"][parent]["commit"] if parent else st["base"]
        c["wt"] = add_worktree(st, cid, start)
    st["candidates"][cid] = c
    return cid


# ---------------------------------------------------------------- jobs

def job_prompt(brief, job_id):
    return ("You are a Crucible sub-agent. Read the brief at %s and follow it exactly. "
            "When finished, reply with one line only: DONE %s" % (brief, job_id))


def phase_jobs(st):
    """The job list of the current LLM phase: {job_id: {brief, outputs}}."""
    d = Path(st["dir"])
    ph = st["phase"]
    jobs = {}
    if ph == "candidates":
        for cid in st["pool"]:
            c = st["candidates"][cid]
            if c["commit"] is None:
                jobs[cid] = {"brief": str(d / "jobs" / (cid + ".md")),
                             "outputs": [str(Path(c["dir"]) / "solution.md")]}
    elif ph == "judge":
        jid = "judge-r%d" % st["round"]
        jobs[jid] = {"brief": str(d / "jobs" / (jid + ".md")),
                     "outputs": [str(d / "judge" / ("r%d" % st["round"]) / "verdict.json")]}
    elif ph == "redteam":
        jobs["redteam"] = {"brief": str(d / "jobs" / "redteam.md"),
                           "outputs": [str(d / "redteam" / "attack.md")]}
    elif ph == "revise":
        outs = [str(d / "revise" / "response.md")]
        if not st["code"]:
            outs.append(str(d / "revise" / "solution.md"))
        jobs["revise"] = {"brief": str(d / "jobs" / "revise.md"), "outputs": outs}
    elif ph == "final":
        jobs["final"] = {"brief": str(d / "jobs" / "final.md"),
                         "outputs": [str(d / "final" / "final.json")]}
    return jobs


def brief_values(st, job_id):
    d = Path(st["dir"])
    v = {"TASK": str(d / "task.md"), "CHECKS": str(d / "checks.md"),
         "CODE": st["code"], "TEST_CMD": st.get("test_cmd") or "",
         "CHECK_SCRIPT": st.get("check_script") or "",
         "N_CHECKS": st["checks_count"], "JOB": job_id}
    return v


DESCRIBE = {"solution.md": "write-up", "answer.md": "answer",
            "notes.md": "author's notes (not part of the answer)", "patch.diff":
            "code changes (patch against the original)", "tests.txt": "test run",
            "response.md": "answers to a review", "tree": "full working tree (read only)"}


def blind_copy(dest, files, tree=None):
    """Copy files under a neutral folder, so that paths reveal nothing about origin."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    lines = []
    for name, src in files:
        if Path(src).exists():
            shutil.copyfile(src, dest / name)
            lines.append("- %s: %s" % (DESCRIBE.get(name, name), dest / name))
    if tree:
        link = dest / "tree"
        if not link.exists():
            os.symlink(tree, link)
        lines.append("- %s: %s" % (DESCRIBE["tree"], link))
    return "\n".join(lines)


def solution_block(st, cid, label, dest):
    c = st["candidates"][cid]
    if st["code"]:
        files = [("solution.md", Path(c["dir"], "solution.md"))]
    else:
        files = [("answer.md", Path(c["dir"], "solution.md")), ("notes.md", Path(c["dir"], "notes.md"))]
    if st["code"]:
        files += [("patch.diff", Path(c["dir"], "patch.diff")), ("tests.txt", Path(c["dir"], "tests.txt"))]
    body = blind_copy(dest, files, c["wt"] if st["code"] else None)
    if c["tests"] is not None:
        body += "\n- tests: %s" % ("PASSED" if c["tests"]["passed"] else "FAILED")
    chk = c.get("checks")
    if chk:
        if chk.get("error"):
            body += "\n- check script: ERROR (%s)" % chk["error"][:200]
        else:
            body += "\n- scripted checks (measured facts, do not re-judge them): %s" % ", ".join(
                "%s %s" % (k, "pass" if v else "FAIL")
                for k, v in sorted(chk["results"].items(), key=lambda kv: int(kv[0])))
    return "### Solution %s\n%s" % (label, body)


def render_brief(st, job_id):
    d = Path(st["dir"])
    ph = st["phase"]
    v = brief_values(st, job_id)
    if ph == "candidates":
        c = st["candidates"][job_id]
        v.update({"APPROACH": c["approach"], "OUT": str(Path(c["dir"]) / "solution.md"),
                  "NOTES": str(Path(c["dir"]) / "notes.md"),
                  "WORKDIR": c["wt"] or "", "REPAIR": c["kind"] == "repair",
                  "LESSONS": c.get("lessons") or "", "PREVIOUS": "",
                  "FEEDBACK": c.get("feedback") or ""})
        if c["kind"] == "repair":
            v["PREVIOUS"] = str(Path(st["candidates"][c["parent"]]["dir"]) / "solution.md")
        text = render(read(BRIEFS / "candidate.md"), v)
    elif ph == "judge":
        pool = list(st["pool"])
        rng = random.Random("%s-%d" % (st["seed"], st["round"]))
        rng.shuffle(pool)
        labels = {chr(65 + i): cid for i, cid in enumerate(pool)}
        st["labels"] = labels
        rdir = d / "judge" / ("r%d" % st["round"])
        v.update({"SOLUTIONS": "\n\n".join(solution_block(st, cid, lab, rdir / lab)
                                            for lab, cid in labels.items()),
                  "LABELS": ", ".join(labels), "OUT": phase_jobs(st)[job_id]["outputs"][0]})
        text = render(read(BRIEFS / "judge.md"), v)
    elif ph == "redteam":
        w = st["candidates"][st["winner"]]
        v.update({"SOLUTION": str(Path(w["dir"]) / "solution.md"),
                  "PATCH": str(Path(w["dir"]) / "patch.diff") if st["code"] else "",
                  "WORKDIR": w["wt"] or "", "OUT": str(d / "redteam" / "attack.md")})
        text = render(read(BRIEFS / "redteam.md"), v)
    elif ph == "revise":
        w = st["candidates"][st["winner"]]
        v.update({"SOLUTION": str(Path(w["dir"]) / "solution.md"),
                  "ATTACK": str(d / "redteam" / "attack.md"),
                  "ATTACK_TESTS": str(d / "redteam" / "tests.txt") if st["code"] and st.get("test_cmd") else "",
                  "GRAFT": str(d / "graft.md") if Path(d / "graft.md").exists() else "",
                  "WORKDIR": w["wt"] or "", "OUT_DIR": str(d / "revise")})
        text = render(read(BRIEFS / "revise.md"), v)
    elif ph == "final":
        opts = final_options(st)
        rng = random.Random("%s-final" % st["seed"])
        keys = list(opts)
        rng.shuffle(keys)
        labels = {chr(65 + i): k for i, k in enumerate(keys)}
        st["labels"] = labels
        blocks = []
        for lab, key in labels.items():
            blocks.append("### Option %s\n%s" % (lab, blind_copy(d / "final" / lab, opts[key])))
        v.update({"OPTIONS": "\n\n".join(blocks), "LABELS": ", ".join(labels),
                  "OUT": str(d / "final" / "final.json")})
        text = render(read(BRIEFS / "final.md"), v)
    else:
        die("no brief for phase " + ph)
    write(phase_jobs(st)[job_id]["brief"], text)


def final_options(st):
    """Candidate deliverables for the final blind comparison."""
    d = Path(st["dir"])
    w = st["candidates"][st["winner"]]
    pending = (st.get("revision") or {}).get("pending_check")
    opts = {}
    if st["code"]:
        opts["pre"] = [("solution.md", Path(w["dir"], "solution.md")),
                       ("patch.diff", Path(w["dir"], "patch.diff"))]
        if pending:
            opts["rev"] = [("solution.md", Path(w["dir"], "solution.md")),
                           ("response.md", d / "revise" / "response.md"),
                           ("patch.diff", d / "revise" / "patch.diff")]
    else:
        opts["pre"] = [("answer.md", Path(w["dir"], "solution.md"))]
        if pending:
            opts["rev"] = [("answer.md", d / "revise" / "solution.md")]
    if st["has_baseline"]:
        opts["baseline"] = [("answer.md", d / "baseline.md")]
    return opts


def show_next(st):
    ph = st["phase"]
    head = "Run %s · phase: %s%s · calls %d/%d" % (
        st["id"], ph, " (wave %d)" % st["wave"] if ph == "candidates" else "",
        st["calls"], st["max_calls"])
    print(head)
    if ph in LLM_PHASES:
        jobs = phase_jobs(st)
        pending = {j: v for j, v in jobs.items()
                   if st["jobs"].get(j, {}).get("state") != "done"}
        to_issue = [j for j in pending if st["jobs"].get(j, {}).get("state") != "issued"]
        if st["calls"] + len(to_issue) > st["max_calls"]:
            print("Budget exhausted: issuing %d more job(s) would exceed the cap." % len(to_issue))
            print("Run: %s" % cmd(st, "collect --partial"))
            return
        for j in to_issue:
            for out in jobs[j]["outputs"]:
                Path(out).parent.mkdir(parents=True, exist_ok=True)
            render_brief(st, j)
            st["jobs"][j] = {"state": "issued", "issued": st["jobs"].get(j, {}).get("issued", 0) + 1}
            st["calls"] += 1
        if to_issue:
            log(st, "issued %s" % ", ".join(to_issue))
        save(st)
        n = len(pending)
        print("Spawn %d sub-agent%s now%s, one per job, each with exactly this prompt:"
              % (n, "s" if n > 1 else "", ", all in parallel" if n > 1 else ""))
        for j, v in pending.items():
            print("  [%s] %s" % (j, job_prompt(v["brief"], j)))
        print("When every one has replied, run: %s" % cmd(st, "collect"))
    elif ph == "draft":
        c = st["candidates"]["c0"]
        n = st["fixes_used"] + 1
        print("Level 0, attempt %d of %d. No sub-agents: you do this yourself." % (n, st["max_fixes"] + 1))
        if st["code"]:
            print("  Make your changes in %s (a private copy of the repository)," % c["wt"])
            print("  and write a short account of them to %s." % Path(c["dir"], "solution.md"))
        else:
            print("  Write the complete answer, and nothing else, to %s." % Path(c["dir"], "solution.md"))
        if n > 1:
            print("  Fix what failed last time: %s" % Path(c["dir"], "feedback.md"))
        print("Then run: %s" % cmd(st, "check"))
    elif ph == "escalate":
        e = estimate(st["k"], st["escalations_left"], st["wave2"], st["code"],
                     bool(st.get("test_cmd")) or not st["code"], st["has_baseline"])
        print("Level 0 did not pass its checks after %d attempt(s): %s"
              % (len(st["attempts"]), Path(st["candidates"]["c0"]["dir"], "feedback.md")))
        print("Level 1 is a tournament: typical %d sub-agent calls, hard cap %d." % (
            e["typical"], st["max_calls"]))
        if st["ask"]:
            print("You started Crucible on your own initiative: ask the user before spending these calls.")
        print("To go on, write %d hypotheses to a file, one bullet each: different explanations of"
              % (st["k"] - 1))
        print("why the answer fails, or different ways to solve it. Then run:")
        print("  %s" % cmd(st, "escalate --hypotheses <file>"))
        print("To stop and deliver the level-0 answer with its open failures: %s" % cmd(st, "finish"))
    elif ph.startswith("verify"):
        print("No sub-agents. Run the tests (this can take a while; run it in the background "
              "if your shell has a short timeout):")
        print("  %s" % cmd(st, "verify"))
    elif ph == "done":
        print("Finished. Read %s and present it to the user." % Path(st["dir"], "RESULT.md"))
        if st["code"] and Path(st["dir"], "final.patch").exists():
            print("Apply only after the user agrees: %s" % cmd(st, "apply"))
        print("Then free the worktrees: %s" % cmd(st, "cleanup"))
        if st["level"] == 0:
            print("If the user still wants a tournament: %s"
                  % cmd(st, "escalate --hypotheses <file>"))


# ---------------------------------------------------------------- level 0

def parse_ids(text):
    ids = set()
    for part in (text or "").replace(" ", "").split(","):
        if part:
            if not part.isdigit():
                die("check numbers must look like 2,5 (got %r)" % text)
            ids.add(int(part))
    return sorted(ids)


def cmd_check(a):
    st = load(find_run(a.run))
    if st["phase"] != "draft":
        die("phase is '%s': `check` is for level 0. Run: %s" % (st["phase"], cmd(st, "next")))
    c = st["candidates"]["c0"]
    sol = Path(c["dir"]) / "solution.md"
    if not sol.exists() or not sol.read_text().strip():
        die("write your answer to %s first" % sol)
    n = st["checks_count"]
    attempt = st["fixes_used"] + 1
    tests = run_tests(st, c["wt"], Path(c["dir"]) / ("tests-%d.txt" % attempt)) if st["code"] else None
    chk = run_checks(st, c, Path(c["dir"]) / ("checks-%d.txt" % attempt))
    scripted = (chk or {}).get("results") or {}
    unscripted = [i for i in range(1, n + 1) if str(i) not in scripted]
    bad_scripted = failed_scripted(chk)

    print("Level 0, attempt %d of %d" % (attempt, st["max_fixes"] + 1))
    if tests is not None:
        print("  tests: %s (%s)" % ("passed" if tests["passed"] else "FAILED", tests["log"]))
    if chk is not None:
        if chk["error"]:
            print("  check script: ERROR, %s" % chk["error"])
        else:
            print("  scripted checks: %s" % (", ".join(
                "%s %s" % (k, "ok" if v else "FAIL")
                for k, v in sorted(scripted.items(), key=lambda kv: int(kv[0]))) or "none"))
    self_failed = parse_ids(a.self_failed) if a.self_failed is not None else None
    hard_fail = (tests is not None and not tests["passed"]) or bad_scripted \
        or bool((chk or {}).get("error"))
    # a measured failure counts at once; only a clean measured run asks for self-review
    if not hard_fail and unscripted and self_failed is None and not a.self_verified:
        print("  checks no script can decide: %s" % ", ".join(map(str, unscripted)))
        print("Now verify those yourself, one by one, against your answer and %s." % (
            Path(st["dir"]) / "checks.md"))
        print("- If one fails: fix your answer and run `check` again (this attempt is not counted).")
        print("- If they all pass: %s" % cmd(st, "check --self-verified"))
        print("- If some still fail and you cannot fix them: %s" % cmd(st, "check --self-failed 2,5"))
        return
    self_failed = [i for i in (self_failed or []) if i in unscripted]

    passed = (tests is None or tests["passed"]) and not bad_scripted \
        and not (chk or {}).get("error") and not self_failed
    c["tests"], c["checks"], c["self_failed"] = tests, chk, self_failed
    st["attempts"].append({"attempt": attempt, "tests_ok": tests is None or tests["passed"],
                           "failed_scripted": bad_scripted, "self_failed": self_failed,
                           "script_error": bool((chk or {}).get("error"))})
    if passed:
        log(st, "level 0 passed on attempt %d" % attempt)
        snapshot_candidate(st, "c0")
        st["winner"] = "c0"
        st["phase"] = "done"
        finish(st)
        save(st)
        print("All checks pass.")
        print()
        show_next(st)
        return

    checks = numbered_items(read(Path(st["dir"]) / "checks.md"))
    fb = ["# What failed in the level-0 answer (attempt %d)" % attempt, ""]
    if tests is not None and not tests["passed"]:
        fb.append("- the tests FAIL: %s" % tests["log"])
    if (chk or {}).get("error"):
        fb.append("- the check script could not score the answer: %s" % chk["error"])
    for i in bad_scripted + self_failed:
        fb.append("- check %d fails%s: %s" % (i, " (measured by the script)" if i in bad_scripted
                                             else " (by the author's own reading)", checks[i - 1]))
    write(Path(c["dir"]) / "feedback.md", "\n".join(fb) + "\n")
    st["fixes_used"] += 1
    log(st, "level 0 attempt %d failed: %s" % (attempt, "; ".join(fb[2:])[:300]))
    if st["fixes_used"] > st["max_fixes"]:
        st["phase"] = "escalate"
    save(st)
    print("Some checks fail: %s" % (Path(c["dir"]) / "feedback.md"))
    print()
    show_next(st)


def snapshot_candidate(st, cid):
    c = st["candidates"][cid]
    if st["code"]:
        c["commit"] = snapshot(st, c["wt"], "crucible %s" % cid)
        c["stat"] = write_patch(st, c["wt"], c["commit"], Path(c["dir"]) / "patch.diff")
    else:
        c["commit"] = "text"


def cmd_escalate(a):
    st = load(find_run(a.run))
    from_done = st["phase"] == "done" and st["level"] == 0
    if st["phase"] != "escalate" and not from_done:
        die("phase is '%s': nothing to escalate. Run: %s" % (st["phase"], cmd(st, "next")))
    hyps = list_items(read(a.hypotheses))
    k = st["k"]
    if len(hyps) < k - 1:
        die("need %d hypotheses, found %d in %s" % (k - 1, len(hyps), a.hypotheses))
    if not can_afford(st, k + 1):
        die("the call cap (%d) cannot pay for %d candidates and a judge" % (st["max_calls"], k))
    write(Path(st["dir"]) / "hypotheses.md", read(a.hypotheses))
    c0 = st["candidates"]["c0"]
    if c0["commit"] is None:
        snapshot_candidate(st, "c0")
    feedback = Path(c0["dir"]) / "feedback.md"
    if not feedback.exists():
        write(feedback, "# The level-0 answer passed its checks\n\nThe user asked for a "
                        "tournament anyway: look for what the checks do not cover.\n")
    st.update(level=1, winner=None, outcome=None, wave=1, phase="candidates")
    new = [new_candidate(st, "Repair the first attempt: keep what works, fix exactly what the "
                         "feedback reports.", "repair", parent="c0", feedback=str(feedback))]
    for h in hyps[:k - 1]:
        new.append(new_candidate(st, h, "fresh", lessons=str(feedback)))
    st["pool"] = ["c0"] + new
    log(st, "escalate to level 1: %s, plus the level-0 answer" % ", ".join(new))
    save(st)
    show_next(st)


def cmd_finish(a):
    st = load(find_run(a.run))
    if st["phase"] != "escalate":
        die("phase is '%s': `finish` ends a level-0 run that failed its checks" % st["phase"])
    snapshot_candidate(st, "c0")
    st["winner"] = "c0"
    st["phase"] = "done"
    log(st, "stopped at level 0 with open failures")
    finish(st)
    save(st)
    show_next(st)


# ---------------------------------------------------------------- collect

def missing_outputs(st):
    out = {}
    for j, v in phase_jobs(st).items():
        miss = [p for p in v["outputs"] if not Path(p).exists() or not Path(p).read_text().strip()]
        if miss:
            out[j] = miss
    return out


def cmd_collect(a):
    st = load(find_run(a.run))
    ph = st["phase"]
    if ph not in LLM_PHASES:
        die("phase is '%s': nothing to collect. Run: %s" % (ph, cmd(st, "next")))
    miss = missing_outputs(st)
    # malformed JSON counts as missing
    for j, v in phase_jobs(st).items():
        for p in v["outputs"]:
            if p.endswith(".json") and j not in miss and Path(p).exists():
                try:
                    json.loads(read(p))
                except ValueError as e:
                    miss[j] = ["%s (invalid JSON: %s)" % (p, e)]
    if miss and not a.partial:
        for j in phase_jobs(st):
            if j in miss:
                st["jobs"][j] = {"state": "missing",
                                 "issued": st["jobs"].get(j, {}).get("issued", 1)}
            else:
                st["jobs"][j] = {"state": "done"}
        log(st, "missing outputs: %s" % ", ".join(miss))
        save(st)
        print("Missing or invalid outputs:")
        for j, ps in miss.items():
            print("  [%s] %s" % (j, "; ".join(ps)))
        print("Run `next` to re-issue them (each costs a call), or `collect --partial` to go on without.")
        print("  %s" % cmd(st, "next"))
        return
    for j in phase_jobs(st):
        if j not in miss:
            st["jobs"][j] = {"state": "done"}
    handler = {"candidates": collect_candidates, "judge": collect_judge,
               "redteam": collect_redteam, "revise": collect_revise,
               "final": collect_final}[ph]
    handler(st, set(miss))
    st["jobs"] = {}
    if st["phase"] == "done":
        finish(st)
    save(st)
    show_next(st)


def collect_candidates(st, missing):
    present = [cid for cid in st["pool"] if cid not in missing]
    for cid in missing:
        st["pool"].remove(cid)
        log(st, "%s dropped: no solution" % cid)
    if not st["pool"]:
        die("no candidate produced a solution; nothing to judge")
    for cid in present:
        c = st["candidates"][cid]
        if st["code"] and c["commit"] is None:
            c["commit"] = snapshot(st, c["wt"], "crucible %s" % cid)
            c["stat"] = write_patch(st, c["wt"], c["commit"], Path(c["dir"]) / "patch.diff")
        elif not st["code"]:
            c["commit"] = "text"
    log(st, "wave %d collected: %s" % (st["wave"], ", ".join(present)))
    if (st["code"] and st.get("test_cmd")) or st.get("check_script"):
        st["phase"] = "verify"
    else:
        start_judge(st)


def start_judge(st):
    if len(st["pool"]) == 1:
        # nothing to compare: the lone survivor leads, with no checklist evidence
        cid = st["pool"][0]
        st["leader"] = cid
        log(st, "single candidate %s: judge skipped" % cid)
        choose_winner(st, cid, clean=False, consensus=False)
        return
    st["round"] += 1
    st["phase"] = "judge"


def merged_checks(st, c, sol):
    """{check number: pass}: the script's measurement where it exists, else the judge's."""
    judged = {}
    for i, x in enumerate(sol.get("checks") or []):
        if isinstance(x, dict):
            judged[str(x.get("id", i + 1))] = bool(x.get("pass"))
        else:
            judged[str(i + 1)] = bool(x)
    scripted = (c.get("checks") or {}).get("results") or {}
    return {str(i): scripted.get(str(i), judged.get(str(i), False))
            for i in range(1, st["checks_count"] + 1)}


def candidate_key(st, cid, sol, rank):
    c = st["candidates"][cid]
    tests_ok = c["tests"]["passed"] if c["tests"] is not None else True
    script_ok = not (c.get("checks") or {}).get("error")
    passes = sum(merged_checks(st, c, sol).values())
    fatal = len(sol.get("fatal") or [])
    return (tests_ok, script_ok, fatal == 0, passes, -rank), passes, fatal, tests_ok and script_ok


def collect_judge(st, missing):
    rdir = Path(st["dir"]) / "judge" / ("r%d" % st["round"])
    verdict = {}
    if not missing:
        verdict = json.loads(read(rdir / "verdict.json"))
    sols = verdict.get("solutions") or {}
    ranking = [l for l in (verdict.get("ranking") or []) if l in st["labels"]]
    ranking += [l for l in st["labels"] if l not in ranking]
    scored = []
    for lab, cid in st["labels"].items():
        key, passes, fatal, tests_ok = candidate_key(st, cid, sols.get(lab, {}), ranking.index(lab))
        scored.append((key, cid, lab, passes, fatal, tests_ok))
    scored.sort(reverse=True)
    summary = [{"cid": cid, "label": lab, "checks_passed": p, "fatal": f, "tests_ok": t}
               for _, cid, lab, p, f, t in scored]
    st["verdicts"].append({"round": st["round"], "labels": st["labels"], "order": summary,
                           "consensus": bool(verdict.get("consensus")),
                           "judge_missing": bool(missing)})
    top = scored[0]
    leader, lead_lab, passes, fatal, tests_ok = top[1], top[2], top[3], top[4], top[5]
    st["leader"] = leader
    clean = (not missing) and passes >= st["checks_count"] and fatal == 0 and tests_ok
    log(st, "judge r%d: leader %s (checks %d/%d, fatal %d, tests %s)%s" % (
        st["round"], leader, passes, st["checks_count"], fatal,
        "ok" if tests_ok else "FAILED", " · consensus" if verdict.get("consensus") else ""))

    # material for later briefs, written in the judge's words but without labels
    if verdict.get("graft"):
        write(Path(st["dir"]) / "graft.md", str(verdict["graft"]) + "\n")
    if verdict.get("lessons"):
        write(rdir / "lessons.md", str(verdict["lessons"]) + "\n")
    lead_sol = sols.get(lead_lab, {})
    c = st["candidates"][leader]
    fb = ["# What was found wrong with the previous best solution", ""]
    scripted = (c.get("checks") or {}).get("results") or {}
    for i in failed_scripted(c.get("checks")):
        fb.append("- check %d failed (measured by the check script)" % i)
    for x in lead_sol.get("checks") or []:
        if isinstance(x, dict) and not x.get("pass") and str(x.get("id")) not in scripted:
            fb.append("- check %s failed: %s" % (x.get("id", "?"), x.get("evidence", "")))
    for f in lead_sol.get("fatal") or []:
        fb.append("- fatal flaw: %s" % f)
    if c["tests"] is not None and not c["tests"]["passed"]:
        fb.append("- tests FAILED, log: %s" % c["tests"]["log"])
    write(rdir / "feedback.md", "\n".join(fb) + "\n")

    if not clean and st["escalations_left"] > 0 and can_afford(st, st["wave2"] + 1 + 2):
        st["escalations_left"] -= 1
        st["wave"] += 1
        lessons = rdir / "lessons.md"
        if not lessons.exists():
            write(lessons, "The judge left no general lessons. Read %s.\n" % (rdir / "feedback.md"))
        new = [new_candidate(st, "Repair the previous best solution: keep what works, fix "
                             "exactly what the feedback reports.", "repair", parent=leader,
                             feedback=str(rdir / "feedback.md"))]
        for _ in range(st["wave2"] - 1):
            new.append(new_candidate(st, "A fresh solution that avoids the failures in the "
                                     "lessons file. Do not reuse the earlier designs.", "fresh",
                                     lessons=str(lessons)))
        st["pool"] = [leader] + new
        st["phase"] = "candidates"
        log(st, "escalate: wave %d with %s" % (st["wave"], ", ".join(new)))
        return
    choose_winner(st, leader, clean, bool(verdict.get("consensus")))


def can_afford(st, n):
    return st["calls"] + n <= st["max_calls"]


def needs_final_after_revision(st):
    return st["has_baseline"] or not st["code"] or not st.get("test_cmd")


def choose_winner(st, cid, clean, consensus):
    # Consensus does not skip the red team: candidates from one model share
    # blind spots, and agreement is exactly where those hide. The attack costs
    # one call; the revision runs only if the attack finds something real.
    st["winner"] = cid
    reserve = 1 if clean else 2 + (1 if needs_final_after_revision(st) else 0)
    if can_afford(st, reserve):
        st["phase"] = "redteam"
    else:
        log(st, "not enough budget for the red team (%d calls left)" % (st["max_calls"] - st["calls"]))
        to_final_or_done(st)


def to_final_or_done(st):
    pending = (st.get("revision") or {}).get("pending_check")
    if (st["has_baseline"] or pending) and can_afford(st, 1):
        st["phase"] = "final"
    else:
        if pending:
            # cannot afford the check: never deliver an unverified revision
            st["revision"]["accepted"] = False
            st["revision"]["pending_check"] = False
            log(st, "no budget to check the revision: delivering the pre-revision winner")
        st["phase"] = "done"


def parse_severity(text):
    m = re.search(r"SEVERITY:\s*FATAL\s*=\s*(\d+)\s*MAJOR\s*=\s*(\d+)\s*MINOR\s*=\s*(\d+)", text)
    if m:
        return {"fatal": int(m.group(1)), "major": int(m.group(2)), "minor": int(m.group(3))}
    # fall back to counting labelled findings
    return {k: len(re.findall(r"\b%s\b" % k.upper(), text)) for k in ("fatal", "major", "minor")}


def collect_redteam(st, missing):
    if missing:
        st["redteam"] = {"skipped": True}
        log(st, "red team produced nothing")
        to_final_or_done(st)
        return
    sev = parse_severity(read(Path(st["dir"]) / "redteam" / "attack.md"))
    st["redteam"] = dict(sev, confirmed=None)
    log(st, "red team: FATAL %d MAJOR %d MINOR %d" % (sev["fatal"], sev["major"], sev["minor"]))
    if st["code"] and st.get("test_cmd"):
        st["phase"] = "verify_attack"
    else:
        after_attack(st)


def after_attack(st):
    sev = st["redteam"]
    if sev["fatal"] + sev["major"] == 0 and not (sev.get("confirmed")):
        if st["code"]:
            reset_winner(st)
        st["revision"] = {"skipped": True}
        log(st, "no FATAL or MAJOR finding: revision skipped")
        to_final_or_done(st)
    elif can_afford(st, 1 + (1 if needs_final_after_revision(st) else 0)):
        st["phase"] = "revise"
    else:
        if st["code"]:
            reset_winner(st)
        st["revision"] = {"skipped": True, "reason": "budget"}
        to_final_or_done(st)


def reset_winner(st):
    w = st["candidates"][st["winner"]]
    git(["reset", "-q", "--hard", w["commit"]], w["wt"])
    git(["clean", "-q", "-fd"], w["wt"])


def collect_revise(st, missing):
    d = Path(st["dir"])
    if missing:
        if st["code"]:
            reset_winner(st)
        st["revision"] = {"accepted": False, "reason": "reviser produced nothing"}
        to_final_or_done(st)
        return
    w = st["candidates"][st["winner"]]
    if st["code"]:
        commit = snapshot(st, w["wt"], "crucible revision of %s" % st["winner"])
        write_patch(st, w["wt"], commit, d / "revise" / "patch.diff")
        st["revision"] = {"commit": commit, "accepted": None, "pending_check": False}
        if st.get("test_cmd") or st.get("check_script"):
            st["phase"] = "verify_revise"
            return
    else:
        st["revision"] = {"accepted": None, "pending_check": False}
        chk = run_checks(st, w, d / "revise" / "checks.txt", answer=d / "revise" / "solution.md")
        if chk is not None:
            st["revision"]["checks"] = chk
            if worse_checks(w.get("checks"), chk):
                st["revision"].update(accepted=False, reason="it fails scripted checks the original passed")
                log(st, "revision rejected by the check script")
                to_final_or_done(st)
                return
    st["revision"]["pending_check"] = True
    to_final_or_done(st)


def collect_final(st, missing):
    if missing:
        res = {"ranking": [], "reasons": "final judge produced nothing"}
    else:
        res = json.loads(read(Path(st["dir"]) / "final" / "final.json"))
    ranking = [st["labels"][l] for l in (res.get("ranking") or []) if l in st["labels"]]
    st["final"] = {"ranking": ranking, "labels": st["labels"],
                   "reasons": res.get("reasons", "")}
    rev = st.get("revision") or {}
    if rev.get("pending_check"):
        better = ("rev" in ranking and "pre" in ranking
                  and ranking.index("rev") < ranking.index("pre"))
        rev["accepted"] = better
        rev["pending_check"] = False
        if not better and st["code"]:
            reset_winner(st)
        log(st, "final judge: revision %s" % ("accepted" if better else "rejected"))
    if st["has_baseline"] and "baseline" in ranking:
        st["final"]["baseline_won"] = ranking[0] == "baseline"
        log(st, "final judge: baseline ranked %d of %d" % (ranking.index("baseline") + 1,
                                                           len(ranking)))
    st["phase"] = "done"


# ---------------------------------------------------------------- verify

def cmd_verify(a):
    st = load(find_run(a.run))
    ph = st["phase"]
    if not ph.startswith("verify"):
        die("phase is '%s': nothing to verify. Run: %s" % (ph, cmd(st, "next")))
    if st["code"] and st.get("main_status") is not None and main_tree_status(st) != st["main_status"]:
        msg = "WARNING: the main working tree changed since init; a sub-agent may have edited it"
        log(st, msg)
        print(msg)
    if ph == "verify":
        for cid in st["pool"]:
            c = st["candidates"][cid]
            if c["tests"] is None and st["code"] and st.get("test_cmd"):
                c["tests"] = run_tests(st, c["wt"], Path(c["dir"]) / "tests.txt")
                print("%s: tests %s" % (cid, "passed" if c["tests"]["passed"] else "FAILED"))
                log(st, "%s tests %s" % (cid, "passed" if c["tests"]["passed"] else "failed"))
            if c.get("checks") is None and st.get("check_script"):
                c["checks"] = run_checks(st, c, Path(c["dir"]) / "checks.txt")
                bad = failed_scripted(c["checks"])
                msg = "script error" if c["checks"]["error"] else (
                    "checks %s fail" % ",".join(map(str, bad)) if bad else "scripted checks pass")
                print("%s: %s" % (cid, msg))
                log(st, "%s %s" % (cid, msg))
        start_judge(st)
    elif ph == "verify_attack":
        w = st["candidates"][st["winner"]]
        r = run_tests(st, w["wt"], Path(st["dir"]) / "redteam" / "tests.txt")
        st["redteam"]["confirmed"] = not r["passed"]
        print("attack %s by the tests" % ("CONFIRMED" if not r["passed"] else "not confirmed"))
        log(st, "attack %s by tests" % ("confirmed" if not r["passed"] else "not confirmed"))
        after_attack(st)
    elif ph == "verify_revise":
        w = st["candidates"][st["winner"]]
        r = run_tests(st, w["wt"], Path(st["dir"]) / "revise" / "tests.txt")
        chk = run_checks(st, w, Path(st["dir"]) / "revise" / "checks.txt")
        rev = st["revision"]
        rev["checks"] = chk
        ok = (r is None or r["passed"]) and not worse_checks(w.get("checks"), chk)
        if not ok:
            rev["accepted"] = False
            rev["reason"] = "it fails the tests or a check the original passed"
            reset_winner(st)
            print("revision rejected: keeping the pre-revision winner")
        elif r is None:
            rev["pending_check"] = True      # no tests: a blind judge must confirm it
            print("revision passes the scripted checks; a blind judge will compare it")
        else:
            rev["accepted"] = True
            print("revision passes the tests: accepted")
        log(st, "revision %s" % ("rejected" if not ok else "accepted" if r else "pending judge"))
        to_final_or_done(st)
    if st["phase"] == "done":
        finish(st)
    save(st)
    print()
    show_next(st)


# ---------------------------------------------------------------- result

def finish(st):
    d = Path(st["dir"])
    w = st["candidates"][st["winner"]] if st["winner"] else None
    rev = st.get("revision") or {}
    final = st.get("final") or {}
    lines = ["# Crucible result", ""]
    if not w:
        lines.append("No winner.")
        write(d / "RESULT.md", "\n".join(lines) + "\n")
        st["outcome"] = "no-winner"
        return
    use_rev = bool(rev.get("accepted"))
    if st["code"]:
        commit = rev["commit"] if use_rev else w["commit"]
        stat = write_patch(st, w["wt"], commit, d / "final.patch")
        deliverable = str(d / "final.patch")
    else:
        src = d / "revise" / "solution.md" if use_rev else Path(w["dir"]) / "solution.md"
        shutil.copyfile(src, d / "final.md")
        deliverable = str(d / "final.md")
        stat = None
    last = st["verdicts"][-1]["order"][0] if st["verdicts"] else {}
    st["outcome"] = "baseline-won" if final.get("baseline_won") else "winner"

    lines.append("- **Deliverable:** %s" % deliverable)
    if st["level"] == 0:
        at = st["attempts"][-1] if st["attempts"] else {}
        open_ = sorted(set(at.get("failed_scripted", []) + at.get("self_failed", [])))
        lines.append("- **Level 0:** answered and checked by the host, no sub-agent calls, "
                     "%d attempt(s)" % len(st["attempts"]))
        if open_ or not at.get("tests_ok", True) or at.get("script_error"):
            st["outcome"] = "open-failures"
            lines.append("- **Open failures:** %s%s%s. Delivered as it is, at the user's request." % (
                "checks " + ", ".join(map(str, open_)) if open_ else "",
                "; tests fail" if not at.get("tests_ok", True) else "",
                "; the check script errored" if at.get("script_error") else ""))
        else:
            measured = len((w.get("checks") or {}).get("results") or {})
            lines.append("- **Checks:** all %d pass (%s)" % (
                st["checks_count"],
                "all measured by the script" if measured == st["checks_count"] else
                "%d measured by the script, %d verified by the host" % (
                    measured, st["checks_count"] - measured)))
    else:
        lines += [
            "- **Winner:** %s (wave %d, %s)" % (st["winner"], w["wave"], w["kind"]),
            "- **Hypothesis:** %s" % w["approach"],
            "- **Checks passed (last judge):** %s/%d" % (last.get("checks_passed", "?"),
                                                         st["checks_count"]),
        ]
        bad = failed_scripted(w.get("checks"))
        if w.get("checks") and not use_rev:
            lines.append("- **Scripted checks:** %s" % (
                "fail: " + ", ".join(map(str, bad)) if bad else "all pass"))
    if st["code"]:
        t = w["tests"]
        lines.append("- **Tests:** %s" % ("none configured" if not st.get("test_cmd") else
                                         "passed" if (t and t["passed"]) or use_rev else "FAILED"))
    rt = st.get("redteam")
    if st["level"] == 0:
        pass
    elif rt and not rt.get("skipped"):
        lines.append("- **Red team:** FATAL %d · MAJOR %d · MINOR %d%s" % (
            rt["fatal"], rt["major"], rt["minor"],
            "" if rt.get("confirmed") is None else
            (" · confirmed by tests" if rt["confirmed"] else " · not confirmed by tests")))
        lines.append("  findings: %s" % (d / "redteam" / "attack.md"))
    else:
        lines.append("- **Red team:** skipped")
    if st["level"] == 0:
        pass
    elif rev.get("skipped"):
        lines.append("- **Revision:** not needed")
    elif rev:
        lines.append("- **Revision:** %s" % ("accepted" if rev.get("accepted") else
                                             "rejected (%s)" % rev.get("reason", "did not beat the original")))
    if st["has_baseline"] and final.get("ranking"):
        if final.get("baseline_won"):
            lines.append("- **Baseline:** the answer you rejected ranked FIRST in a blind comparison. "
                         "Keep it; this run did not beat it.")
        else:
            lines.append("- **Baseline:** beaten in a blind comparison")
        if final.get("reasons"):
            lines.append("  reasons: %s" % str(final["reasons"]).strip().replace("\n", " ")[:600])
    lines.append("- **Calls:** %d sub-agent calls of a %d cap" % (st["calls"], st["max_calls"]))
    if stat:
        lines += ["", "```", stat, "```"]
    lines += ["", "## Timeline", ""] + ["- " + x for x in st["log"]]
    write(d / "RESULT.md", "\n".join(lines) + "\n")


def cmd_next(a):
    st = load(find_run(a.run))
    show_next(st)


def cmd_status(a):
    st = load(find_run(a.run))
    print("run %s · level %d · %s · phase %s · calls %d/%d · seed %d" % (
        st["id"], st["level"], st["mode"], st["phase"], st["calls"], st["max_calls"], st["seed"]))
    for cid, c in st["candidates"].items():
        t = c["tests"]
        print("  %s wave %d %-6s tests %-7s %s%s" % (
            cid, c["wave"], c["kind"], "-" if t is None else ("pass" if t["passed"] else "FAIL"),
            c["approach"][:70], "  <- winner" if cid == st["winner"] else ""))
    for line in st["log"][-8:]:
        print("  " + line)


def cmd_report(a):
    st = load(find_run(a.run))
    if st["phase"] != "done":
        die("run not finished (phase %s)" % st["phase"])
    finish(st)
    save(st)
    print(read(Path(st["dir"]) / "RESULT.md"))


def cmd_apply(a):
    st = load(find_run(a.run))
    patch = Path(st["dir"]) / "final.patch"
    if st["phase"] != "done" or not patch.exists():
        die("nothing to apply")
    if main_tree_status(st) != st.get("main_status"):
        die("the working tree changed since the run started; apply by hand: git apply --3way %s" % patch)
    if not read(patch).strip():
        print("the winning patch is empty: nothing to apply")
        return
    git(["apply", "--whitespace=nowarn", str(patch)], st["root"])
    log(st, "final.patch applied to the working tree")
    save(st)
    print("applied %s" % patch)


def cmd_cleanup(a):
    st = load(find_run(a.run))
    for c in st["candidates"].values():
        if c.get("wt") and Path(c["wt"]).exists():
            git(["worktree", "remove", "--force", c["wt"]], st["root"], check=False)
    if st["code"]:
        git(["worktree", "prune"], st["root"], check=False)
    if a.purge:
        shutil.rmtree(st["dir"])
        print("removed %s" % st["dir"])
    else:
        print("worktrees removed; run files kept in %s" % st["dir"])


# ---------------------------------------------------------------- cli

def main(argv=None):
    p = argparse.ArgumentParser(prog="crucible.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("plan", help="print the call budget, write nothing")
    sp.add_argument("--deep", action="store_true")
    sp.add_argument("--tournament", action="store_true")
    sp.add_argument("--candidates", type=int)
    sp.add_argument("--max-calls", type=int)
    sp.add_argument("--max-fixes", type=int, default=2)
    sp.add_argument("--code", action="store_true")
    sp.add_argument("--test-cmd")
    sp.add_argument("--baseline", action="store_true")
    sp.set_defaults(fn=cmd_plan)

    sp = sub.add_parser("init", help="start a run")
    sp.add_argument("--task", required=True)
    sp.add_argument("--checks", required=True)
    sp.add_argument("--check-script", help="Python script that scores the checks it can "
                    "(argument: the answer file; prints {\"<check>\": true|false})")
    sp.add_argument("--hypotheses", "--approaches", dest="hypotheses",
                    help="one bullet per candidate; needed only to start with a tournament")
    sp.add_argument("--baseline")
    sp.add_argument("--code", action="store_true", help="candidates edit code in git worktrees")
    sp.add_argument("--test-cmd", help="shell command that exits 0 when the code is good")
    sp.add_argument("--setup-cmd", help="run once in each new worktree; {root} = repo root")
    sp.add_argument("--test-timeout", type=int, default=600)
    sp.add_argument("--tournament", action="store_true", help="skip level 0")
    sp.add_argument("--deep", action="store_true", help="a bigger tournament; skips level 0")
    sp.add_argument("--max-fixes", type=int, default=2, help="level-0 fixes before the tournament")
    sp.add_argument("--ask", action="store_true",
                    help="the host started Crucible on its own: ask the user before a tournament")
    sp.add_argument("--candidates", type=int)
    sp.add_argument("--max-calls", type=int)
    sp.add_argument("--seed", type=int)
    sp.add_argument("--root")
    sp.set_defaults(fn=cmd_init)

    sp = sub.add_parser("check", help="level 0: score your answer against the checks")
    sp.add_argument("--run")
    sp.add_argument("--self-verified", action="store_true",
                    help="you checked the unscripted checks yourself and they pass")
    sp.add_argument("--self-failed", metavar="N,N", help="unscripted checks that still fail")
    sp.set_defaults(fn=cmd_check)

    sp = sub.add_parser("escalate", help="go to the level-1 tournament")
    sp.add_argument("--run")
    sp.add_argument("--hypotheses", required=True)
    sp.set_defaults(fn=cmd_escalate)

    for name, fn, hlp in (("next", cmd_next, "what to do now"),
                          ("finish", cmd_finish, "stop at level 0 and deliver the answer as it is"),
                          ("collect", cmd_collect, "ingest sub-agent outputs and advance"),
                          ("verify", cmd_verify, "run the tests and advance"),
                          ("status", cmd_status, "show the run"),
                          ("report", cmd_report, "rewrite and print RESULT.md"),
                          ("apply", cmd_apply, "apply final.patch to the working tree"),
                          ("cleanup", cmd_cleanup, "remove the worktrees")):
        sp = sub.add_parser(name, help=hlp)
        sp.add_argument("--run", help="run directory (default: latest run here)")
        if name == "collect":
            sp.add_argument("--partial", action="store_true",
                            help="go on with the outputs that exist")
        if name == "cleanup":
            sp.add_argument("--purge", action="store_true", help="also delete the run files")
        sp.set_defaults(fn=fn)

    a = p.parse_args(argv)
    try:
        a.fn(a)
    except CrucibleError as e:
        print("crucible: " + str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
