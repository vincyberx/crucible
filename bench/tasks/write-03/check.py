#!/usr/bin/env python3
"""Scripted rubric checks for write-03. Prints {"criterion": pass} for the
criteria a script can decide; the rest are left to the model judge.

The schedule is read line by line: the first line that names a step (S1-S9)
and carries a date and a time schedules that step. Later lines that mention a
step with a date (explanations such as "S7 cannot be before 2026-11-18") are
ignored. If the plan cannot be read that way, only the criteria that do not
need it are decided."""

import datetime as dt
import json
import re
import sys

START = dt.datetime(2026, 11, 9, 9, 0)


def words(text):
    return [t for t in text.split() if re.search(r"[A-Za-z0-9]", t)]


def schedule(text):
    steps = {}
    for line in text.splitlines():
        s = re.search(r"\bS([1-9])\b", line)
        # a date with its time close after it ("2026-11-24 02:00", "2026-11-09 (Mon) | 09:00"),
        # so a date quoted in an explanation on the same line is not taken for the schedule
        m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b\D{0,20}?\b(\d{2}):(\d{2})\b", line)
        if s and m and ("S" + s.group(1)) not in steps:
            steps["S" + s.group(1)] = dt.datetime(*map(int, m.groups()))
    return steps


def main(path):
    text = open(path, encoding="utf-8").read()
    out = {"8": len(words(text)) <= 300}
    s = schedule(text)
    if sorted(s) != ["S%d" % i for i in range(1, 10)]:
        print(json.dumps(out))       # unreadable plan: leave 1-7 to the judge
        return
    out["1"] = all(w >= START for w in s.values())
    out["2"] = (s["S8"] < min(s["S1"], s["S3"], s["S5"], s["S7"]) and s["S1"] < s["S2"] < s["S3"]
                and s["S9"] >= s["S3"] + dt.timedelta(hours=2)
                and s["S9"] < min(s["S4"], s["S5"]) and max(s["S4"], s["S5"]) < s["S6"] < s["S7"])
    deploys = [s["S2"], s["S4"], s["S6"]]
    out["3"] = (all(w.weekday() <= 3 and dt.time(9) <= w.time() <= dt.time(16) for w in deploys)
                and len({w.date() for w in deploys}) == 3)
    locks = [s["S5"], s["S7"]]
    out["4"] = (all(w.weekday() == 1 and dt.time(2) <= w.time() <= dt.time(3) for w in locks)
                and s["S5"].date() != s["S7"].date())
    out["5"] = (s["S7"].date() - s["S6"].date()).days >= 7
    last = [l for l in text.strip().splitlines() if l.strip()][-1].strip().strip("*_` ")
    out["6"] = s["S7"].date() == dt.date(2026, 11, 24) and last == "Completion: 2026-11-24"
    # 7 (S7 marked irreversible) is left to the judge: the mark can sit anywhere near S7
    print(json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1])
