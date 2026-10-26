#!/usr/bin/env python3
"""Scripted rubric checks for write-02. Prints {"criterion": pass} for the
criteria a script can decide; the rest are left to the model judge."""

import json
import re
import sys

LABELS = ["Summary", "Impact", "Duration", "Root cause", "Detection", "Action items"]


def words(text):
    # whitespace-separated tokens with at least one letter or digit: a lone
    # bullet "-" or "**" is not a word
    return [t for t in text.split() if re.search(r"[A-Za-z0-9]", t)]


def labels_in_order(text):
    found = []
    for line in text.splitlines():
        m = re.match(r"^\s*(?:#+\s*)?(?:[-*]\s+)?[*_]*\s*([A-Za-z ]+?)\s*[*_]*\s*:", line)
        if m and m.group(1).strip() in LABELS:
            found.append(m.group(1).strip())
    return found == LABELS


def times_ok(text):
    if "CEST" in text:
        return False
    for m in re.finditer(r"\b\d{2}:\d{2}\b", text):
        if not re.match(r"\s*UTC\b", text[m.end():]):
            return False
    return bool(re.search(r"\b49\s*(?:minutes|min)\b", text)) and \
        "07:55 UTC" in text and "08:44 UTC" in text


def main(path):
    text = open(path, encoding="utf-8").read()
    out = {
        "1": len(words(text)) <= 200,
        "2": labels_in_order(text),
        "3": times_ok(text),
        "4": bool(re.search(r"\b2,?371\b", text)) and not re.search(r"\b3,?000\b", text),
        "5": not re.search(r"Priya|Nair|Marco|Bellini", text),
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1])
