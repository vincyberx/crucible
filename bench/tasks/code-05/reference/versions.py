"""Version comparison and sorting. Reference implementation."""

import functools
import re

_NUM = r"(?:0|[1-9][0-9]*)"
_IDENT = r"[0-9A-Za-z-]+"
_VERSION = re.compile(
    rf"({_NUM})\.({_NUM})\.({_NUM})"
    rf"(?:-({_IDENT}(?:\.{_IDENT})*))?"
    rf"(?:\+({_IDENT}(?:\.{_IDENT})*))?"
)
_DIGITS = re.compile(r"[0-9]+")


def _parse(version):
    if not isinstance(version, str):
        raise ValueError(f"not a version: {version!r}")
    m = _VERSION.fullmatch(version)
    if not m:
        raise ValueError(f"invalid version: {version!r}")
    major, minor, patch, pre, _build = m.groups()
    pre_ids = []
    if pre is not None:
        for ident in pre.split("."):
            if _DIGITS.fullmatch(ident):
                if len(ident) > 1 and ident[0] == "0":
                    raise ValueError(f"leading zero in {version!r}")
                pre_ids.append((0, int(ident), ""))
            else:
                pre_ids.append((1, 0, ident))
    return (int(major), int(minor), int(patch)), pre_ids


def _cmp(x, y):
    return (x > y) - (x < y)


def _compare_parsed(pa, pb):
    (core_a, pre_a), (core_b, pre_b) = pa, pb
    c = _cmp(core_a, core_b)
    if c:
        return c
    if not pre_a and not pre_b:
        return 0
    if not pre_a:
        return 1
    if not pre_b:
        return -1
    for ia, ib in zip(pre_a, pre_b):
        c = _cmp(ia, ib)  # (kind, number, text): numeric kind 0 < alnum kind 1
        if c:
            return c
    return _cmp(len(pre_a), len(pre_b))


def compare(a, b):
    return _compare_parsed(_parse(a), _parse(b))


def sort_versions(versions):
    parsed = [(_parse(v), v) for v in versions]
    parsed.sort(key=functools.cmp_to_key(lambda x, y: _compare_parsed(x[0], y[0])))
    return [v for _, v in parsed]
