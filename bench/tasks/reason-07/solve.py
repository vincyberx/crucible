"""Exact solver for reason-07: two-week payroll with overlapping overtime rules.

Works in quarter hours (every time in the timesheet is on a quarter hour) and in integer
cents. Each worked quarter collects every multiplier it qualifies for (R3-R6) and is paid
at the highest one (R7).
"""

from datetime import date, datetime, timedelta

BASE_CENTS_PER_HOUR = 2560
HOLIDAY = date(2026, 11, 13)

# (start, end, [unpaid breaks]) - local times, end exclusive
SHIFTS = [
    ("2026-11-03 07:00", "2026-11-03 17:30", [("2026-11-03 12:00", "2026-11-03 12:30")]),
    ("2026-11-04 08:00", "2026-11-04 16:00", []),
    ("2026-11-05 06:00", "2026-11-05 20:30", [("2026-11-05 13:00", "2026-11-05 13:30")]),
    ("2026-11-06 20:00", "2026-11-07 06:00", []),
    ("2026-11-07 14:00", "2026-11-07 22:00", []),
    ("2026-11-08 09:00", "2026-11-08 17:00", []),
    ("2026-11-09 08:00", "2026-11-09 17:00", []),
    ("2026-11-10 08:00", "2026-11-10 16:00", []),
    ("2026-11-11 07:00", "2026-11-11 18:00", [("2026-11-11 12:00", "2026-11-11 13:00")]),
    ("2026-11-12 22:00", "2026-11-13 07:00", []),
    ("2026-11-13 15:00", "2026-11-13 21:00", []),
    ("2026-11-14 08:00", "2026-11-14 18:30", [("2026-11-14 12:30", "2026-11-14 13:00")]),
    ("2026-11-15 10:00", "2026-11-15 19:00", []),
]

Q_PER_HOUR = 4


def parse(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def worked_quarters():
    """Start instant of every worked quarter hour, in chronological order (R2)."""
    out = []
    for start, end, breaks in SHIFTS:
        t, end = parse(start), parse(end)
        brk = [(parse(a), parse(b)) for a, b in breaks]
        while t < end:
            if not any(a <= t < b for a, b in brk):
                out.append(t)
            t += timedelta(minutes=15)
    return sorted(out)


def monday_of(d):
    return d - timedelta(days=d.weekday())


def main():
    qs = worked_quarters()
    mults = [[1.0] for _ in qs]

    # R3: daily classification by position within the calendar day
    pos_in_day = []
    seen = {}
    for t in qs:
        k = seen.get(t.date(), 0)
        seen[t.date()] = k + 1
        pos_in_day.append(k)
    daily_regular = [k < 8 * Q_PER_HOUR for k in pos_in_day]
    for i, k in enumerate(pos_in_day):
        if 8 * Q_PER_HOUR <= k < 12 * Q_PER_HOUR:
            mults[i].append(1.5)
        elif k >= 12 * Q_PER_HOUR:
            mults[i].append(2.0)

    # R4: weekly overtime on daily-regular quarters past the 40th hour of the workweek
    counted = {}
    for i, t in enumerate(qs):
        if not daily_regular[i]:
            continue
        w = monday_of(t.date())
        counted[w] = counted.get(w, 0) + 1
        if counted[w] > 40 * Q_PER_HOUR:
            mults[i].append(1.5)

    # R5: Sunday of a workweek in which all seven days were worked
    days = {}
    for t in qs:
        days.setdefault(monday_of(t.date()), set()).add(t.date())
    seventh = {w + timedelta(days=6) for w, ds in days.items() if len(ds) == 7}
    for i, t in enumerate(qs):
        if t.date() in seventh:
            mults[i].append(1.5 if pos_in_day[i] < 8 * Q_PER_HOUR else 2.0)

    # R6: holiday
    for i, t in enumerate(qs):
        if t.date() == HOLIDAY:
            mults[i].append(1.75)

    # R7: highest multiplier only; quarter of 2560 = 640, so every product is exact
    total = 0
    for m in mults:
        cents = BASE_CENTS_PER_HOUR * max(m) / Q_PER_HOUR
        assert cents == int(cents)
        total += int(cents)
    print(total)


if __name__ == "__main__":
    main()
