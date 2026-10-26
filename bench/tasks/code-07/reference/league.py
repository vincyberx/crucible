"""League standings with head-to-head tie-breaks (reference implementation)."""


def _table(matches, teams=None):
    """points, goal difference, goals scored per team, from the given matches only.

    With `teams`, only matches in which both teams belong to `teams` are counted.
    """
    pts, gd, gf = {}, {}, {}
    for home, away, hg, ag in matches:
        if teams is not None and (home not in teams or away not in teams):
            continue
        for t in (home, away):
            pts.setdefault(t, 0)
            gd.setdefault(t, 0)
            gf.setdefault(t, 0)
        gf[home] += hg
        gf[away] += ag
        gd[home] += hg - ag
        gd[away] += ag - hg
        if hg > ag:
            pts[home] += 3
        elif hg < ag:
            pts[away] += 3
        else:
            pts[home] += 1
            pts[away] += 1
    return pts, gd, gf


def _group_by(teams, key):
    """Split `teams` into lists of equal key, best (highest key) first."""
    groups = {}
    for t in teams:
        groups.setdefault(key(t), []).append(t)
    return [groups[k] for k in sorted(groups, reverse=True)]


def standings(matches):
    matches = list(matches)
    pts, gd, gf = _table(matches)

    def tie_break(level):
        if len(level) == 1:
            return list(level)
        members = set(level)
        mpts, mgd, mgf = _table(matches, members)
        groups = _group_by(level, lambda t: (mpts.get(t, 0), mgd.get(t, 0), mgf.get(t, 0)))
        if len(groups) == 1:
            # Step 1 separated nobody: step 3, overall criteria, then name.
            return sorted(level, key=lambda t: (-gd[t], -gf[t], t))
        out = []
        for g in groups:
            out.extend(tie_break(g))  # step 2: apply again from step 1, these teams only
        return out

    result = []
    for level in _group_by(sorted(pts), lambda t: pts[t]):
        result.extend(tie_break(level))
    return result
