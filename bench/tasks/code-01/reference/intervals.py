"""Union of intervals written as strings like "[1,5)". Reference implementation."""

import re

_PATTERN = re.compile(r"^([\[\(])\s*(-?\d+)\s*,\s*(-?\d+)\s*([\]\)])$")


def _parse(spec):
    if not isinstance(spec, str):
        raise ValueError(f"bad interval: {spec!r}")
    m = _PATTERN.fullmatch(spec)
    if not m:
        raise ValueError(f"bad interval: {spec!r}")
    left, start, end, right = m.groups()
    start, end = int(start), int(end)
    if start > end:
        raise ValueError(f"start > end in {spec!r}")
    return start, end, left == "[", right == "]"


def _fmt(start, end, left_closed, right_closed):
    return f"{'[' if left_closed else '('}{start},{end}{']' if right_closed else ')'}"


def union(specs):
    items = []
    for spec in specs:
        start, end, lc, rc = _parse(spec)
        if start == end and not (lc and rc):
            continue  # empty interval
        items.append((start, end, lc, rc))
    # Sort by start; at equal start a closed bound comes first.
    items.sort(key=lambda iv: (iv[0], not iv[2]))

    out = []
    for start, end, lc, rc in items:
        if out:
            p_start, p_end, p_lc, p_rc = out[-1]
            if start < p_end or (start == p_end and (p_rc or lc)):
                if end > p_end:
                    p_end, p_rc = end, rc
                elif end == p_end:
                    p_rc = p_rc or rc
                if start == p_start:
                    p_lc = p_lc or lc
                out[-1] = (p_start, p_end, p_lc, p_rc)
                continue
        out.append((start, end, lc, rc))
    return [_fmt(*iv) for iv in out]
