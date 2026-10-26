"""League standings."""


def standings(matches):
    """Return team names ranked from first to last."""
    pts, gd, gf = {}, {}, {}
    for home, away, hg, ag in matches:
        for team in (home, away):
            pts.setdefault(team, 0)
            gd.setdefault(team, 0)
            gf.setdefault(team, 0)
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
    return sorted(pts, key=lambda t: (-pts[t], -gd[t], -gf[t], t))
