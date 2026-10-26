"""Union of intervals written as strings like "[1,5)"."""

import re

_PATTERN = re.compile(r"^([\[\(])(-?\d+),(-?\d+)([\]\)])$")


def _parse(spec):
    m = _PATTERN.match(spec)
    if not m:
        raise ValueError(f"bad interval: {spec!r}")
    left, start, end, right = m.groups()
    return int(start), int(end), left == "[", right == "]"


def _fmt(start, end, left_closed, right_closed):
    return f"{'[' if left_closed else '('}{start},{end}{']' if right_closed else ')'}"


def union(specs):
    items = sorted(_parse(s) for s in specs)
    out = []
    for start, end, lc, rc in items:
        if out and start <= out[-1][1]:
            p_start, p_end, p_lc, p_rc = out[-1]
            if end > p_end:
                out[-1] = (p_start, end, p_lc, rc)
        else:
            out.append((start, end, lc, rc))
    return [_fmt(*iv) for iv in out]
