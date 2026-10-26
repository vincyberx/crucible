#!/usr/bin/env python3
"""Compare two arms of a benchmark run on one task.

Primary outcome: a run "passes" when it meets every criterion (score 1.0).
Test: Fisher's exact test, two-sided, on the 2x2 table of passes and fails.

  python3 bench/stats.py bench/results/<run> --task write-02 [--a single --b crucible]
"""

import argparse
import json
from math import comb
from pathlib import Path


def fisher_two_sided(a_pass, a_fail, b_pass, b_fail):
    """p-value of Fisher's exact test: the probability, with the margins fixed,
    of a table at least as unlikely as the one observed."""
    n_a, n_b = a_pass + a_fail, b_pass + b_fail
    passes, n = a_pass + b_pass, n_a + n_b

    def p(k):  # probability that arm A has k of the passes
        return comb(n_a, k) * comb(n_b, passes - k) / comb(n, passes)

    observed = p(a_pass)
    lo, hi = max(0, passes - n_b), min(passes, n_a)
    return min(1.0, sum(p(k) for k in range(lo, hi + 1) if p(k) <= observed * (1 + 1e-9)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("results")
    ap.add_argument("--task", required=True)
    ap.add_argument("--a", default="single")
    ap.add_argument("--b", default="crucible")
    args = ap.parse_args()
    rows = [r for r in json.loads((Path(args.results) / "results.json").read_text())
            if r["task"] == args.task and r.get("score") is not None]
    table = {}
    for arm in (args.a, args.b):
        rs = [r for r in rows if r["arm"] == arm]
        passed = sum(1 for r in rs if r["score"] == 1.0)
        cost = sum(r.get("cost_usd") or 0 for r in rs) / max(1, len(rs))
        mins = sum(r.get("seconds", 0) for r in rs) / max(1, len(rs)) / 60
        table[arm] = (passed, len(rs) - passed)
        print("%-9s passed %2d of %2d  mean score %.3f  mean cost $%.2f  mean %.1f min" % (
            arm, passed, len(rs), sum(r["score"] for r in rs) / max(1, len(rs)), cost, mins))
    p = fisher_two_sided(*table[args.a], *table[args.b])
    print("Fisher's exact test, two-sided: p = %.4f (%s at 0.05)" % (
        p, "significant" if p < 0.05 else "not significant"))


if __name__ == "__main__":
    main()
