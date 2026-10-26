"""End-to-end tests for crucible.py with stand-in sub-agents.

Each test drives the script through its command line, and plays the
sub-agents by writing the files their briefs ask for.
"""

import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "crucible"))
import crucible  # noqa: E402


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = crucible.main([str(a) for a in argv])
    return code, out.getvalue() + err.getvalue()


def jobs_in(text):
    """[(job_id, brief_path)] from the output of next/collect/verify."""
    return re.findall(r"\[([\w-]+)\] .*?Read the brief at (\S+) and follow", text)


def outputs_of(text):
    return [p for p in re.findall(r"`(/[^`]+)`", text)]


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                           "-c", "commit.gpgsign=false"] + list(args),
                          cwd=cwd, capture_output=True, text=True, check=True).stdout


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name).resolve()
        self.old = os.getcwd()
        self.old_home = os.environ.get("CRUCIBLE_HOME")
        os.environ["CRUCIBLE_HOME"] = str(self.dir / "crucible-home")
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self.old)
        if self.old_home is None:
            os.environ.pop("CRUCIBLE_HOME", None)
        else:
            os.environ["CRUCIBLE_HOME"] = self.old_home
        self.tmp.cleanup()

    def draft(self, n_approaches=3, checks=("Says hello", "Says goodbye")):
        d = self.dir / "draft"
        d.mkdir(exist_ok=True)
        (d / "task.md").write_text("Write a greeting.\n")
        (d / "checks.md").write_text("".join("%d. %s\n" % (i + 1, c) for i, c in enumerate(checks)))
        (d / "approaches.md").write_text("".join("- approach %d\n" % i for i in range(n_approaches)))
        return d

    def init(self, *extra, n_approaches=3, tournament=True):
        d = self.draft(n_approaches)
        args = ["init", "--task", d / "task.md", "--checks", d / "checks.md", "--seed", 7]
        if tournament:
            args += ["--tournament", "--hypotheses", d / "approaches.md"]
        code, out = run(*(args + list(extra)))
        self.assertEqual(code, 0, out)
        return out

    def check_script(self, body=None):
        """A check script that measures check 1: the answer says hello."""
        p = self.dir / "draft" / "check.py"
        p.parent.mkdir(exist_ok=True)
        p.write_text(body or (
            "import json, sys\n"
            "t = open(sys.argv[1]).read().lower()\n"
            "print(json.dumps({'1': 'hello' in t}))\n"))
        return p

    def c0(self):
        return Path(self.state()["candidates"]["c0"]["dir"]) / "solution.md"

    def state(self):
        return crucible.load(crucible.find_run(None))

    def brief_out(self, brief, name):
        """The output path the brief asks for, ending with `name`."""
        for p in outputs_of(Path(brief).read_text()):
            if p.endswith(name):
                return Path(p)
        m = re.search(r"(/\S+%s)" % re.escape(name), Path(brief).read_text())
        if m:
            return Path(m.group(1))
        self.fail("%s not found in %s" % (name, brief))

    def verdict(self, brief, passes, ranking=None, consensus=False, fatal=None, graft="", lessons=""):
        """passes: {label: [bool per check]}"""
        sols = {lab: {"checks": [{"id": i + 1, "pass": p, "evidence": "x"} for i, p in enumerate(ps)],
                      "fatal": (fatal or {}).get(lab, [])} for lab, ps in passes.items()}
        out = self.brief_out(brief, "verdict.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"solutions": sols, "ranking": ranking or list(passes),
                                   "consensus": consensus, "graft": graft, "lessons": lessons}))

    def label_of(self, cid):
        st = self.state()
        return {v: k for k, v in st["labels"].items()}[cid]


class TestHelpers(unittest.TestCase):
    def test_render_blocks_and_vars(self):
        t = "a{{#X}} x={{X}}{{/X}}{{^X}} none{{/X}}{{#Y}}{{#Z}} z{{/Z}}{{/Y}}."
        self.assertEqual(crucible.render(t, {"X": "1", "Y": True, "Z": True}), "a x=1 z.")
        self.assertEqual(crucible.render(t, {"X": "", "Y": False, "Z": True}), "a none.")
        with self.assertRaises(crucible.CrucibleError):
            crucible.render("{{NOPE}}", {})

    def test_lists(self):
        self.assertEqual(crucible.numbered_items("1. a\n2) b\n- c\n"), ["a", "b"])
        self.assertEqual(crucible.list_items("- a\n  more\n* b\n3. c\n"), ["a more", "b", "c"])

    def test_severity(self):
        self.assertEqual(crucible.parse_severity("SEVERITY: FATAL=1 MAJOR=0 MINOR=2\n"),
                         {"fatal": 1, "major": 0, "minor": 2})
        self.assertEqual(crucible.parse_severity("## [MAJOR] x\n## [MINOR] y")["major"], 1)

    def test_estimate(self):
        self.assertEqual(crucible.estimate(3, 1, 2, False, True, False),
                         {"fastest": 5, "typical": 7, "worst": 10})
        self.assertEqual(crucible.estimate(3, 1, 2, True, True, False)["typical"], 6)
        self.assertEqual(crucible.estimate(5, 2, 2, False, True, False)["worst"], 15)

    def test_every_brief_renders(self):
        """No placeholder in any brief is left without a value, in any mode."""
        names = ["TASK", "CHECKS", "CODE", "TEST_CMD", "N_CHECKS", "JOB", "APPROACH", "OUT",
                 "WORKDIR", "REPAIR", "LESSONS", "PREVIOUS", "FEEDBACK", "SOLUTIONS", "LABELS",
                 "SOLUTION", "PATCH", "ATTACK", "ATTACK_TESTS", "GRAFT", "OUT_DIR", "OPTIONS",
                 "NOTES", "CHECK_SCRIPT"]
        for brief in (ROOT / "skills" / "crucible" / "briefs").glob("*.md"):
            for flag in (True, False):
                v = {n: ("v" if flag else "") for n in names}
                text = crucible.render(brief.read_text(), v)
                self.assertNotIn("{{", text, brief.name)


class TestTextRuns(Base):
    def test_consensus_still_gets_a_red_team(self):
        out = self.init()
        jobs = jobs_in(out)
        self.assertEqual([j for j, _ in jobs], ["c1", "c2", "c3"])
        for _, brief in jobs:
            self.assertIn("notes.md", Path(brief).read_text())
            self.brief_out(brief, "solution.md").write_text("Hello and goodbye.\n")
            self.brief_out(brief, "notes.md").write_text("Check 1 met by line 1.\n")
        code, out = run("collect")
        self.assertEqual(code, 0, out)
        (jid, brief), = jobs_in(out)
        self.assertEqual(jid, "judge-r1")
        text = Path(brief).read_text()
        self.assertIn("author's notes (not part of the answer)", text)
        self.assertNotIn("approach", text)          # the judge never sees the cards
        self.assertNotIn("/candidates/", text)      # nor paths that reveal who is who
        self.verdict(brief, {l: [True, True] for l in "ABC"}, consensus=True)
        code, out = run("collect")
        (jid, brief), = jobs_in(out)
        self.assertEqual(jid, "redteam")      # agreement is where shared blind spots hide
        self.brief_out(brief, "attack.md").write_text("SEVERITY: FATAL=0 MAJOR=0 MINOR=1\n")
        code, out = run("collect")
        self.assertIn("Finished", out)       # nothing real found: no revision
        st = self.state()
        self.assertEqual(st["calls"], 5)
        self.assertTrue(st["revision"]["skipped"])
        final = Path(st["dir"]) / "final.md"
        self.assertEqual(final.read_text(), "Hello and goodbye.\n")
        self.assertIn("5 sub-agent calls", (Path(st["dir"]) / "RESULT.md").read_text())

    def test_escalation_redteam_revision(self):
        out = self.init()
        for cid, brief in jobs_in(out):
            self.brief_out(brief, "solution.md").write_text("Hello from %s.\n" % cid)
        _, out = run("collect")
        (_, brief), = jobs_in(out)
        # nobody says goodbye: c2 leads on ranking, the round is not clean
        self.verdict(brief, {l: [True, False] for l in "ABC"},
                     ranking=[self.label_of("c2"), self.label_of("c1"), self.label_of("c3")],
                     lessons="Everyone forgot goodbye.", graft="Use a warm tone.")
        _, out = run("collect")
        jobs = jobs_in(out)
        self.assertEqual([j for j, _ in jobs], ["c4", "c5"])
        st = self.state()
        self.assertEqual(st["candidates"]["c4"]["kind"], "repair")
        self.assertEqual(st["candidates"]["c4"]["parent"], "c2")
        self.assertIn("Everyone forgot goodbye", Path(self.brief_out(jobs[1][1], "lessons.md")).read_text())
        for cid, brief in jobs:
            self.brief_out(brief, "solution.md").write_text("Hello and goodbye from %s.\n" % cid)
        _, out = run("collect")
        (jid, brief), = jobs_in(out)
        self.assertEqual(jid, "judge-r2")
        self.assertEqual(sorted(self.state()["pool"]), ["c2", "c4", "c5"])
        self.verdict(brief, {self.label_of("c2"): [True, False], self.label_of("c4"): [True, True],
                             self.label_of("c5"): [True, True]},
                     ranking=[self.label_of("c5"), self.label_of("c4"), self.label_of("c2")])
        _, out = run("collect")
        self.assertEqual(self.state()["winner"], "c5")   # checks tie, judge rank decides
        (jid, brief), = jobs_in(out)
        self.assertEqual(jid, "redteam")
        self.brief_out(brief, "attack.md").write_text(
            "SEVERITY: FATAL=0 MAJOR=1 MINOR=0\n## [MAJOR] too short\n")
        _, out = run("collect")
        (jid, brief), = jobs_in(out)
        self.assertEqual(jid, "revise")
        st = self.state()
        rdir = Path(st["dir"]) / "revise"
        rdir.mkdir(exist_ok=True)
        (rdir / "response.md").write_text("CONCEDED: longer now\n")
        (rdir / "solution.md").write_text("Hello, dear friend, and goodbye.\n")
        _, out = run("collect")
        (jid, brief), = jobs_in(out)
        self.assertEqual(jid, "final")
        st = self.state()
        rev = {v: k for k, v in st["labels"].items()}["rev"]
        pre = {v: k for k, v in st["labels"].items()}["pre"]
        out_path = self.brief_out(brief, "final.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps({"ranking": [rev, pre], "reasons": "warmer"}))
        _, out = run("collect")
        self.assertIn("Finished", out)
        st = self.state()
        self.assertTrue(st["revision"]["accepted"])
        self.assertEqual((Path(st["dir"]) / "final.md").read_text(), "Hello, dear friend, and goodbye.\n")
        self.assertLessEqual(st["calls"], st["max_calls"])
        self.assertEqual(st["calls"], 10)

    def test_baseline_can_win(self):
        (self.dir / "base.md").write_text("Old answer.\n")
        out = self.init("--baseline", self.dir / "base.md")
        for _, brief in jobs_in(out):
            self.brief_out(brief, "solution.md").write_text("New answer.\n")
        _, out = run("collect")
        (_, brief), = jobs_in(out)
        self.verdict(brief, {l: [True, True] for l in "ABC"}, consensus=True)
        _, out = run("collect")
        (_, brief), = jobs_in(out)
        self.brief_out(brief, "attack.md").write_text("SEVERITY: FATAL=0 MAJOR=0 MINOR=0\n")
        _, out = run("collect")
        (jid, brief), = jobs_in(out)
        self.assertEqual(jid, "final")
        st = self.state()
        base = {v: k for k, v in st["labels"].items()}["baseline"]
        others = [k for k in st["labels"] if k != base]
        p = self.brief_out(brief, "final.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"ranking": [base] + others, "reasons": "old was better"}))
        _, out = run("collect")
        st = self.state()
        self.assertEqual(st["outcome"], "baseline-won")
        self.assertIn("ranked FIRST", (Path(st["dir"]) / "RESULT.md").read_text())

    def test_missing_output_is_reissued_and_charged(self):
        out = self.init()
        jobs = jobs_in(out)
        for _, brief in jobs[:2]:
            self.brief_out(brief, "solution.md").write_text("x\n")
        _, out = run("collect")
        self.assertIn("Missing", out)
        _, out = run("next")
        self.assertEqual([j for j, _ in jobs_in(out)], ["c3"])
        self.assertEqual(self.state()["calls"], 4)
        _, out = run("next")                                  # re-printing is free
        self.assertEqual(self.state()["calls"], 4)
        _, out = run("collect", "--partial")
        self.assertEqual(self.state()["pool"], ["c1", "c2"])
        self.assertEqual(self.state()["phase"], "judge")

    def test_budget_cap_is_never_exceeded(self):
        out = self.init("--max-calls", 5)
        for _, brief in jobs_in(out):
            self.brief_out(brief, "solution.md").write_text("x\n")
        _, out = run("collect")
        (_, brief), = jobs_in(out)
        self.verdict(brief, {l: [False, False] for l in "ABC"})
        _, out = run("collect")
        st = self.state()
        # no room for a second wave nor a red team: deliver the leader
        self.assertEqual(st["phase"], "done")
        self.assertEqual(st["calls"], 4)

    def test_foreign_run_is_refused(self):
        """A state file that came with a cloned repo must not get its commands run."""
        self.init()
        st = self.state()
        planted = json.loads((Path(st["dir"]) / "state.json").read_text())
        planted.update(phase="verify", test_cmd="touch PWNED", token="forged")
        (Path(st["dir"]) / "state.json").write_text(json.dumps(planted))
        code, out = run("verify")
        self.assertEqual(code, 2)
        self.assertIn("refusing", out)
        self.assertFalse((self.dir / "PWNED").exists())
        (self.dir / ".crucible" / "latest").write_text("../../etc\n")
        code, out = run("next")
        self.assertIn("does not name a run", out)

    def test_init_validates(self):
        d = self.draft(n_approaches=2)
        code, out = run("init", "--task", d / "task.md", "--checks", d / "checks.md",
                        "--tournament", "--approaches", d / "approaches.md")
        self.assertEqual(code, 2)
        self.assertIn("needs 3 hypotheses", out)
        (d / "checks.md").write_text("- not numbered\n")
        code, out = run("init", "--task", d / "task.md", "--checks", d / "checks.md")
        self.assertIn("no numbered items", out)


class TestLevelZero(Base):
    def test_passes_with_script_and_self_review(self):
        out = self.init("--check-script", self.check_script(), tournament=False)
        self.assertIn("Level 0, attempt 1 of 3", out)
        self.assertEqual(self.state()["phase"], "draft")
        self.c0().write_text("Hello and goodbye.\n")
        code, out = run("check")
        self.assertIn("scripted checks: 1 ok", out)
        self.assertIn("checks no script can decide: 2", out)
        self.assertEqual(self.state()["phase"], "draft")       # waits for the self-review
        self.assertEqual(self.state()["fixes_used"], 0)
        code, out = run("check", "--self-verified")
        self.assertIn("Finished", out)
        st = self.state()
        self.assertEqual((st["calls"], st["winner"], st["level"]), (0, "c0", 0))
        self.assertEqual((Path(st["dir"]) / "final.md").read_text(), "Hello and goodbye.\n")
        result = (Path(st["dir"]) / "RESULT.md").read_text()
        self.assertIn("Level 0", result)
        self.assertIn("1 measured by the script, 1 verified by the host", result)

    def test_check_script_is_frozen(self):
        script = self.check_script()
        self.init("--check-script", script, tournament=False)
        script.write_text("import json\nprint(json.dumps({'1': True}))\n")   # tampering
        self.c0().write_text("Goodbye.\n")
        _, out = run("check")
        self.assertIn("1 FAIL", out)

    def test_failures_count_then_escalate_to_hypotheses(self):
        self.init("--check-script", self.check_script(), tournament=False)
        for attempt in (1, 2, 3):
            self.c0().write_text("Goodbye only.\n")
            _, out = run("check")                      # a measured failure counts at once
            self.assertIn("Some checks fail", out)
        st = self.state()
        self.assertEqual(st["phase"], "escalate")
        fb = (Path(st["candidates"]["c0"]["dir"]) / "feedback.md").read_text()
        self.assertIn("check 1 fails (measured by the script)", fb)
        self.assertIn("Says hello", fb)
        hyp = self.dir / "draft" / "hyp.md"
        hyp.write_text("- the greeting is missing\n- the tone is wrong\n")
        _, out = run("escalate", "--hypotheses", hyp)
        st = self.state()
        self.assertEqual(st["level"], 1)
        self.assertEqual(st["pool"], ["c0", "c1", "c2", "c3"])
        self.assertEqual(st["candidates"]["c1"]["kind"], "repair")
        jobs = jobs_in(out)
        self.assertEqual([j for j, _ in jobs], ["c1", "c2", "c3"])   # c0 is already written
        repair = Path(jobs[0][1]).read_text()
        self.assertIn("feedback.md", repair)
        self.assertIn("c0/solution.md", repair)
        self.assertIn("the greeting is missing", Path(jobs[1][1]).read_text())
        self.assertIn("check.py", repair)                 # candidates can self-check
        # c1 is the judge's favourite but fails the script: the measurement wins
        for cid, brief in jobs:
            text = "Goodbye.\n" if cid == "c1" else "Hello, goodbye.\n"
            self.brief_out(brief, "solution.md").write_text(text)
        _, out = run("collect")
        self.assertIn("verify", out)
        _, out = run("verify")
        (jid, brief), = jobs_in(out)
        self.assertIn("scripted checks (measured facts", Path(brief).read_text())
        labels = {v: k for k, v in self.state()["labels"].items()}
        self.verdict(brief, {labels[c]: [True, True] for c in ("c0", "c1", "c2", "c3")},
                     ranking=[labels["c1"], labels["c0"], labels["c2"], labels["c3"]])
        _, out = run("collect")
        self.assertEqual(self.state()["winner"], "c2")

    def test_finish_with_open_failures(self):
        self.init("--check-script", self.check_script(), "--max-fixes", 0, tournament=False)
        self.c0().write_text("Goodbye.\n")
        run("check")
        self.assertEqual(self.state()["phase"], "escalate")
        _, out = run("finish")
        st = self.state()
        self.assertEqual((st["phase"], st["outcome"]), ("done", "open-failures"))
        self.assertIn("Open failures:** checks 1", (Path(st["dir"]) / "RESULT.md").read_text())

    def test_self_failed_counts(self):
        self.init(tournament=False)
        self.c0().write_text("Hello.\n")
        _, out = run("check")
        self.assertIn("checks no script can decide: 1, 2", out)
        _, out = run("check", "--self-failed", "2")
        st = self.state()
        self.assertEqual(st["fixes_used"], 1)
        self.assertEqual(st["attempts"][0]["self_failed"], [2])

    def test_escalate_after_success(self):
        self.init(tournament=False)
        self.c0().write_text("Hello and goodbye.\n")
        run("check", "--self-verified")
        self.assertEqual(self.state()["phase"], "done")
        hyp = self.dir / "draft" / "hyp.md"
        hyp.write_text("- a\n- b\n")
        _, out = run("escalate", "--hypotheses", hyp)
        self.assertEqual(self.state()["phase"], "candidates")
        self.assertEqual(len(jobs_in(out)), 3)

    def test_revision_rejected_by_the_script(self):
        self.init("--check-script", self.check_script())
        for _, brief in jobs_in(run("next")[1]):
            self.brief_out(brief, "solution.md").write_text("Hello, goodbye.\n")
        run("collect")
        _, out = run("verify")
        (_, brief), = jobs_in(out)
        self.verdict(brief, {l: [True, True] for l in "ABC"})
        _, out = run("collect")
        (_, brief), = jobs_in(out)
        self.brief_out(brief, "attack.md").write_text("SEVERITY: FATAL=0 MAJOR=1 MINOR=0\n")
        _, out = run("collect")
        rdir = Path(self.state()["dir"]) / "revise"
        rdir.mkdir(exist_ok=True)
        (rdir / "response.md").write_text("CONCEDED\n")
        (rdir / "solution.md").write_text("Goodbye, dear.\n")      # loses the greeting
        _, out = run("collect")
        st = self.state()
        self.assertIn("Finished", out)                              # no final judge needed
        self.assertFalse(st["revision"]["accepted"])
        self.assertEqual((Path(st["dir"]) / "final.md").read_text(), "Hello, goodbye.\n")


TEST_CMD = "python3 -m unittest -q"


class TestCodeRuns(Base):
    def setUp(self):
        super().setUp()
        self.repo = self.dir / "repo"
        self.repo.mkdir()
        (self.repo / "calc.py").write_text("def add(a, b):\n    return a - b\n")
        (self.repo / "test_calc.py").write_text(
            "import unittest\nfrom calc import add\n\n"
            "class T(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n")
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "start")
        # an uncommitted edit must reach the candidates
        (self.repo / "NOTES.txt").write_text("")
        git(self.repo, "add", "NOTES.txt")
        os.chdir(self.repo)

    def wt(self, cid):
        return Path(self.state()["candidates"][cid]["wt"])

    def write_candidates(self, out, good=("c1", "c3")):
        for cid, brief in jobs_in(out):
            wt = self.wt(cid)
            self.assertTrue((wt / "NOTES.txt").exists())
            body = "    return a + b\n" if cid in good else "    return a * b\n"
            (wt / "calc.py").write_text("def add(a, b):\n" + body)
            self.brief_out(brief, "solution.md").write_text("fixed add in %s\n" % cid)

    def test_full_code_run_with_attack_and_revision(self):
        out = self.init("--code", "--test-cmd", TEST_CMD)
        self.assertEqual(git(self.repo, "status", "--porcelain").strip(), "A  NOTES.txt")
        self.write_candidates(out)
        _, out = run("collect")
        self.assertIn("verify", out)
        _, out = run("verify")
        st = self.state()
        self.assertTrue(st["candidates"]["c1"]["tests"]["passed"])
        self.assertFalse(st["candidates"]["c2"]["tests"]["passed"])
        (_, brief), = jobs_in(out)
        self.assertIn("FAILED", Path(brief).read_text())
        self.verdict(brief, {self.label_of(c): [True, True] for c in ("c1", "c2", "c3")},
                     ranking=[self.label_of("c2"), self.label_of("c1"), self.label_of("c3")])
        _, out = run("collect")
        st = self.state()
        self.assertNotEqual(st["winner"], "c2")         # failing tests beat the judge's taste
        win = st["winner"]
        (jid, brief), = jobs_in(out)
        self.assertEqual(jid, "redteam")
        (self.wt(win) / "test_attack.py").write_text(
            "import unittest\nfrom calc import add\n\n"
            "class A(unittest.TestCase):\n    def test_str(self):\n"
            "        self.assertEqual(add('1', 2), 3)\n")
        self.brief_out(brief, "attack.md").write_text("SEVERITY: FATAL=0 MAJOR=1 MINOR=0\n")
        _, out = run("collect")
        _, out = run("verify")
        self.assertIn("CONFIRMED", out)
        (jid, brief), = jobs_in(out)
        self.assertEqual(jid, "revise")
        (self.wt(win) / "calc.py").write_text("def add(a, b):\n    return int(a) + int(b)\n")
        resp = Path(self.state()["dir"]) / "revise" / "response.md"
        resp.parent.mkdir(exist_ok=True)
        resp.write_text("CONCEDED\n")
        _, out = run("collect")
        _, out = run("verify")
        self.assertIn("accepted", out)
        self.assertIn("Finished", out)
        st = self.state()
        self.assertEqual(st["calls"], 6)
        patch = (Path(st["dir"]) / "final.patch").read_text()
        self.assertIn("int(a) + int(b)", patch)
        self.assertIn("test_attack.py", patch)
        code, out = run("apply")
        self.assertEqual(code, 0, out)
        self.assertIn("int(a)", (self.repo / "calc.py").read_text())
        code, out = run("cleanup")
        self.assertFalse(self.wt(win).exists())

    def test_failed_revision_is_thrown_away(self):
        out = self.init("--code", "--test-cmd", TEST_CMD)
        self.write_candidates(out, good=("c1", "c2", "c3"))
        run("collect")
        _, out = run("verify")
        (_, brief), = jobs_in(out)
        self.verdict(brief, {l: [True, False] for l in "ABC"},
                     ranking=[self.label_of("c1"), self.label_of("c2"), self.label_of("c3")])
        _, out = run("collect")     # not clean: second wave
        jobs = jobs_in(out)
        self.assertEqual(len(jobs), 2)
        repair = jobs[0][0]
        self.assertIn("return a + b", (self.wt(repair) / "calc.py").read_text())  # starts from c1
        self.write_candidates(out, good=tuple(j for j, _ in jobs))
        run("collect")
        _, out = run("verify")
        (_, brief), = jobs_in(out)
        self.verdict(brief, {l: [True, True] for l in "ABC"},
                     ranking=[self.label_of("c1")] + [self.label_of(j) for j, _ in jobs])
        _, out = run("collect")
        win = self.state()["winner"]
        self.assertEqual(win, "c1")
        (_, brief), = jobs_in(out)
        self.brief_out(brief, "attack.md").write_text("SEVERITY: FATAL=1 MAJOR=0 MINOR=0\n")
        run("collect")
        _, out = run("verify")
        self.assertIn("not confirmed", out)
        (self.wt(win) / "calc.py").write_text("def add(a, b):\n    return 0\n")   # a bad revision
        resp = Path(self.state()["dir"]) / "revise" / "response.md"
        resp.parent.mkdir(exist_ok=True)
        resp.write_text("CONCEDED\n")
        run("collect")
        _, out = run("verify")
        self.assertIn("rejected", out)
        st = self.state()
        self.assertFalse(st["revision"]["accepted"])
        self.assertIn("return a + b", (self.wt(win) / "calc.py").read_text())
        self.assertIn("return a + b", (Path(st["dir"]) / "final.patch").read_text())
        self.assertLessEqual(st["calls"], st["max_calls"])

    def test_level0_code(self):
        self.init("--code", "--test-cmd", TEST_CMD, tournament=False)
        wt = self.wt("c0")
        self.assertTrue((wt / "NOTES.txt").exists())
        (wt / "calc.py").write_text("def add(a, b):\n    return a * b\n")
        self.c0().write_text("tried\n")
        _, out = run("check")
        self.assertIn("tests: FAILED", out)
        (wt / "calc.py").write_text("def add(a, b):\n    return a + b\n")
        _, out = run("check")
        self.assertIn("checks no script can decide", out)
        _, out = run("check", "--self-verified")
        self.assertIn("Finished", out)
        st = self.state()
        self.assertEqual(st["calls"], 0)
        self.assertIn("return a + b", (Path(st["dir"]) / "final.patch").read_text())
        self.assertEqual(run("apply")[0], 0)
        self.assertIn("a + b", (self.repo / "calc.py").read_text())

    def test_code_needs_git(self):
        os.chdir(self.dir)
        d = self.draft()
        code, out = run("init", "--task", d / "task.md", "--checks", d / "checks.md",
                        "--approaches", d / "approaches.md", "--code", "--root", self.dir / "draft")
        self.assertEqual(code, 2)
        self.assertIn("git repository", out)


if __name__ == "__main__":
    unittest.main()
