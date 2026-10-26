"""Exact solver for reason-09: transit fares with transfers, caps and delay refunds.

Processes the ride log in chronological order exactly as task.md prescribes:
pending refunds first (F7), then journey/transfer classification and cost (F2-F4),
then the daily and weekly caps (F5-F6). All amounts are integer cents.
"""

from datetime import datetime, time, timedelta

FULL_FARE = {1: 200, 2: 300, 3: 400, 4: 500}
CONCESSION_OFF = 80
OFF_PEAK_PERCENT_OFF = 30
WINDOW_MIN = 90
MAX_TRANSFERS = 2
DAILY_CAP = 700
WEEKLY_CAP = 2400

# (start, zones, delayed)
RIDES = [
    ("2026-11-16 08:10", 4, False),
    ("2026-11-16 12:40", 3, False),
    ("2026-11-16 18:00", 2, False),
    ("2026-11-17 07:50", 3, False),
    ("2026-11-17 17:20", 3, True),
    ("2026-11-18 08:30", 4, False),
    ("2026-11-18 18:10", 2, False),
    ("2026-11-19 09:00", 2, False),
    ("2026-11-19 16:45", 4, False),
    ("2026-11-20 08:20", 2, False),
    ("2026-11-20 17:40", 3, False),
    ("2026-11-21 11:00", 3, False),
    ("2026-11-22 23:30", 2, False),
    ("2026-11-23 03:10", 1, False),
    ("2026-11-23 04:10", 3, False),
    ("2026-11-23 08:00", 1, False),
    ("2026-11-23 09:30", 3, False),
    ("2026-11-24 07:40", 1, False),
    ("2026-11-24 08:30", 1, False),
    ("2026-11-24 09:20", 1, False),
    ("2026-11-24 13:00", 2, False),
    ("2026-11-24 13:30", 1, False),
    ("2026-11-24 14:00", 1, False),
    ("2026-11-24 14:20", 2, False),
    ("2026-11-25 07:30", 4, False),
    ("2026-11-25 10:00", 1, False),
    ("2026-11-25 12:00", 3, True),
    ("2026-11-25 17:45", 2, False),
    ("2026-11-26 03:20", 3, False),
    ("2026-11-26 04:30", 2, False),
    ("2026-11-26 08:15", 2, False),
]


def is_peak(dt):
    if dt.weekday() >= 5:
        return False
    t = dt.time()
    return time(7, 0) <= t <= time(9, 29) or time(16, 30) <= t <= time(18, 59)


def price(zones, peak):
    """F3: the lowest price obtainable with a single applicable discount."""
    full = FULL_FARE[zones]
    options = [full - CONCESSION_OFF]
    if not peak:
        off = full * (100 - OFF_PEAK_PERCENT_OFF)
        assert off % 100 == 0
        options.append(off // 100)
    return min(options)


def service_day(dt):
    return (dt - timedelta(hours=4)).date()


def service_week(sd):
    return sd - timedelta(days=sd.weekday())


def main():
    day_count, week_count = {}, {}
    pending = []          # (service day, service week, amount)
    paid = 0
    journey = None        # dict(start, peak, zmax, transfers)
    for start, zones, delayed in RIDES:
        dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
        sd = service_day(dt)
        wk = service_week(sd)
        # F7: refunds of service days that have ended (at 04:00 after them)
        still = []
        for rsd, rwk, amount in pending:
            if rsd < sd:
                paid -= amount
                week_count[rwk] -= amount
            else:
                still.append((rsd, rwk, amount))
        pending = still
        # F4: journey or transfer, and its cost
        is_transfer = (
            journey is not None
            and dt - journey["start"] <= timedelta(minutes=WINDOW_MIN)
            and journey["transfers"] < MAX_TRANSFERS
        )
        if is_transfer:
            journey["transfers"] += 1
            if zones > journey["zmax"]:
                cost = price(zones, journey["peak"]) - price(journey["zmax"], journey["peak"])
                journey["zmax"] = zones
            else:
                cost = 0
        else:
            journey = dict(start=dt, peak=is_peak(dt), zmax=zones, transfers=0)
            cost = price(zones, journey["peak"])
        # F6: caps
        dc, wc = day_count.get(sd, 0), week_count.get(wk, 0)
        charge = max(0, min(cost, DAILY_CAP - dc, WEEKLY_CAP - wc))
        day_count[sd] = dc + charge
        week_count[wk] = wc + charge
        paid += charge
        if delayed:
            pending.append((sd, wk, charge))
    for _, _, amount in pending:  # refunds still due after the last ride
        paid -= amount
    print(paid)


if __name__ == "__main__":
    main()
