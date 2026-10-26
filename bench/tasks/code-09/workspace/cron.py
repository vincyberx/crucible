"""Next fire time of a five-field cron expression."""

import datetime

FIELD_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]


def _parse_field(field, lo, hi):
    values = set()
    for part in field.split(","):
        if "/" in part:
            base, step = part.split("/")
            step = int(step)
        else:
            base, step = part, 1
        if base == "*":
            start, end = 0, hi
        elif "-" in base:
            a, b = base.split("-")
            start, end = int(a), int(b)
        else:
            start = end = int(base)
        for value in range(start, end + 1, step):
            if lo <= value <= hi:
                values.add(value)
    return values


def next_fire(expr, after):
    """Return the first time strictly after `after` at which `expr` fires, or None."""
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError("expected 5 fields")
    minutes, hours, doms, months, dows = (
        _parse_field(f, lo, hi) for f, (lo, hi) in zip(fields, FIELD_RANGES)
    )
    dom_star = fields[2] == "*"
    dow_star = fields[4] == "*"

    t = after.replace(second=0, microsecond=0)
    limit = after + datetime.timedelta(days=366)
    while t <= limit:
        if t.minute in minutes and t.hour in hours and t.month in months:
            dom_ok = t.day in doms
            dow_ok = t.weekday() in dows
            if dom_star or dow_star:
                day_ok = dom_ok and dow_ok
            else:
                day_ok = dom_ok or dow_ok
            if day_ok and t >= after:
                return t
        t += datetime.timedelta(minutes=1)
    return None
