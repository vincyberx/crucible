"""Exact solver for reason-06: league table with recursive head-to-head tiebreakers.

Implements the rules of task.md literally:
- the awarded result replaces the on-pitch score for every purpose;
- the points deduction counts only for the points total (step 1);
- criteria (a)-(c) are applied together to the whole set of teams in question, then
  re-applied from the start to every subset still level on all three, recursively;
- only a set that (a)-(c) cannot split at all falls through to (d) and (e).
"""

TEAMS = ["Bramley", "Ironbridge", "Kestrel", "Lowfield", "Oakham", "Pinecrest",
         "Ravenmoor", "Westbury"]

# (home, away, home goals, away goals) as played on the pitch
MATCHES = [
    ("Kestrel", "Lowfield", 0, 2),
    ("Pinecrest", "Kestrel", 2, 1),
    ("Oakham", "Ironbridge", 2, 1),
    ("Ravenmoor", "Ironbridge", 2, 2),
    ("Bramley", "Ironbridge", 0, 1),
    ("Bramley", "Kestrel", 3, 1),
    ("Ironbridge", "Pinecrest", 1, 1),
    ("Kestrel", "Ravenmoor", 2, 1),
    ("Westbury", "Ironbridge", 0, 0),
    ("Oakham", "Lowfield", 2, 1),
    ("Oakham", "Bramley", 0, 1),
    ("Oakham", "Pinecrest", 1, 1),
    ("Oakham", "Westbury", 0, 0),
    ("Kestrel", "Ironbridge", 0, 1),
    ("Kestrel", "Westbury", 3, 0),
    ("Westbury", "Lowfield", 1, 0),
    ("Oakham", "Ravenmoor", 1, 1),
    ("Pinecrest", "Westbury", 0, 2),
    ("Pinecrest", "Bramley", 1, 1),
    ("Ironbridge", "Lowfield", 2, 3),
    ("Lowfield", "Bramley", 0, 3),
    ("Pinecrest", "Lowfield", 1, 1),
    ("Lowfield", "Ravenmoor", 0, 2),
    ("Ravenmoor", "Bramley", 3, 2),
    ("Pinecrest", "Ravenmoor", 1, 3),
    ("Ravenmoor", "Westbury", 3, 2),
    ("Oakham", "Kestrel", 1, 1),
    ("Westbury", "Bramley", 1, 1),
]

AWARDED = {("Oakham", "Ravenmoor"): (0, 3)}
DEDUCTION = {"Bramley": 2}


def results():
    out = []
    for h, a, hg, ag in MATCHES:
        if (h, a) in AWARDED:
            hg, ag = AWARDED[(h, a)]
        out.append((h, a, hg, ag))
    return out


def table(matches, subset=None):
    """points, goal difference, goals scored, restricted to matches inside `subset`."""
    t = {}
    for h, a, hg, ag in matches:
        if subset is not None and (h not in subset or a not in subset):
            continue
        for team, gf, ga in ((h, hg, ag), (a, ag, hg)):
            row = t.setdefault(team, [0, 0, 0])
            row[0] += 3 if gf > ga else (1 if gf == ga else 0)
            row[1] += gf - ga
            row[2] += gf
    return t


def head_to_head(group, matches, overall):
    if len(group) == 1:
        return list(group)
    h2h = table(matches, set(group))
    key = lambda team: tuple(h2h[team])  # (a), (b), (c) together
    levels = sorted({key(team) for team in group}, reverse=True)
    if len(levels) == 1:
        # (a)-(c) cannot split this set at all: fall through to (d), (e)
        ranked = sorted(group, key=lambda team: (overall[team][1], overall[team][2]),
                        reverse=True)
        keys = [(overall[team][1], overall[team][2]) for team in ranked]
        assert len(set(keys)) == len(keys), "drawing of lots would be needed"
        return ranked
    out = []
    for level in levels:
        cls = [team for team in group if key(team) == level]
        out += head_to_head(cls, matches, overall)  # re-application from the start
    return out


def main():
    matches = results()
    overall = table(matches)
    points = {team: overall[team][0] - DEDUCTION.get(team, 0) for team in TEAMS}
    order = []
    for p in sorted(set(points.values()), reverse=True):
        group = [team for team in TEAMS if points[team] == p]
        order += head_to_head(group, matches, overall)
    print(",".join(order))


if __name__ == "__main__":
    main()
