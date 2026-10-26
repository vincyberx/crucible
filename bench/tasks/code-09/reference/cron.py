"""Next fire time of a five-field cron expression (reference implementation)."""

import datetime

# (minimum, maximum) of each field, in order.
_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]


def _number(text, lo, hi):
    if not text or not all("0" <= c <= "9" for c in text):
        raise ValueError("bad number %r" % text)
    value = int(text)
    if not lo <= value <= hi:
        raise ValueError("value %d out of range %d-%d" % (value, lo, hi))
    return value


def _parse_field(text, lo, hi):
    values = set()
    for item in text.split(","):
        step = 1
        has_step = "/" in item
        if has_step:
            item, step_text = item.split("/", 1)
            if not step_text or not all("0" <= c <= "9" for c in step_text):
                raise ValueError("bad step %r" % step_text)
            step = int(step_text)
            if step < 1:
                raise ValueError("step must be >= 1")
        if item == "*":
            start, end = lo, hi
        elif "-" in item:
            a, b = item.split("-", 1)
            start, end = _number(a, lo, hi), _number(b, lo, hi)
            if start > end:
                raise ValueError("range %r is reversed" % item)
        else:
            if has_step:
                raise ValueError("a step needs '*' or a range")
            start = end = _number(item, lo, hi)
        values.update(range(start, end + 1, step))
    return values


def parse(expr):
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError("expected 5 fields, got %d" % len(fields))
    sets = [_parse_field(f, lo, hi) for f, (lo, hi) in zip(fields, _RANGES)]
    dom_restricted = not fields[2].startswith("*")
    dow_restricted = not fields[4].startswith("*")
    if 7 in sets[4]:
        sets[4].add(0)
    return sets, dom_restricted and dow_restricted


def _day_matches(day, sets, use_or):
    minutes, hours, doms, months, dows = sets
    if day.month not in months:
        return False
    dom_ok = day.day in doms
    dow_ok = (day.weekday() + 1) % 7 in dows  # Monday is weekday() 0, cron 1
    return (dom_ok or dow_ok) if use_or else (dom_ok and dow_ok)


def next_fire(expr, after):
    sets, use_or = parse(expr)
    minutes, hours = sorted(sets[0]), sorted(sets[1])
    end = datetime.date(after.year + 11, 1, 1)
    day = after.date()
    first = True
    while day < end:
        if _day_matches(day, sets, use_or):
            for h in hours:
                for m in minutes:
                    if not first or (h, m) > (after.hour, after.minute):
                        return datetime.datetime(day.year, day.month, day.day, h, m)
        day += datetime.timedelta(days=1)
        first = False
    return None
