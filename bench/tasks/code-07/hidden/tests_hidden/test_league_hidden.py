import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from league import standings  # noqa: E402

NAMES = {"A": "Amber", "B": "Blue", "C": "Coral", "D": "Dune", "E": "Ember", "F": "Fern"}


def m(spec):
    """'A-B 2-1, ...' -> [(home, away, hg, ag), ...] with full team names."""
    out = []
    for item in spec.split(","):
        teams, score = item.split()
        h, a = teams.split("-")
        hg, ag = score.split("-")
        out.append((NAMES[h], NAMES[a], int(hg), int(ag)))
    return out


def names(letters):
    return [NAMES[c] for c in letters]


class TestReapplication(unittest.TestCase):
    def test_reapplied_to_the_two_still_level(self):
        # All four teams have 4 points. Mini-table of the four (= the whole league):
        # Amber (4, +1, 5), Blue (4, +1, 3), Coral (4, -1, 3), Dune (4, -1, 3).
        # Coral and Dune are still level, so step 1 is applied again to {Coral, Dune}
        # alone: Dune won their match 3-1.
        matches = m("B-D 0-0, A-D 3-0, C-A 1-1, B-C 0-1, B-A 3-1, C-D 1-3")
        self.assertEqual(standings(matches), names("ABDC"))

    def test_two_rounds_of_reapplication(self):
        # All five teams have 5 points and goal difference 0. Step 1 on all five
        # separates only Coral (1 goal scored against 2). Step 1 again on
        # {Amber, Blue, Dune, Ember}: Blue 5 pts, Amber 4 (0, 2), Dune 4 (0, 2), Ember 2.
        # Step 1 a third time on {Amber, Dune}: Dune won 1-0.
        matches = m("B-A 1-1, E-D 1-1, D-A 1-0, E-A 0-1, A-C 0-0, "
                    "B-D 1-0, C-D 0-0, E-B 0-0, E-C 1-0, B-C 0-1")
        self.assertEqual(standings(matches), names("BDAEC"))

    def test_double_round_robin(self):
        # All four teams have 8 points and goal difference 0; Dune scored 8, the others 6.
        # Step 1 again on {Amber, Blue, Coral}: Coral 6 pts, Blue 5 (+1), Amber 5 (-1).
        matches = m("C-D 1-1, B-D 2-1, B-A 2-2, A-D 2-0, D-B 2-0, D-A 2-1, "
                    "A-B 0-0, C-A 0-1, A-C 0-2, B-C 0-1, C-B 0-2, D-C 2-2")
        self.assertEqual(standings(matches), names("DCBA"))

    def test_two_separate_level_groups(self):
        matches = m("E-C 2-2, E-F 2-1, A-C 2-2, F-A 1-1, E-D 0-1, A-E 2-2, B-C 0-2, "
                    "D-C 0-0, B-D 2-1, A-B 1-2, A-D 1-0, B-F 0-1, E-B 2-2, F-D 0-1, C-F 0-2")
        self.assertEqual(standings(matches), names("BDFEAC"))


class TestOverallStep(unittest.TestCase):
    def test_overall_step_is_final(self):
        # Amber, Coral and Dune have 4 points; among them a 1-0 cycle, all level.
        # Overall: goal difference 0 for all three; goals scored Amber 2, Coral 2, Dune 1.
        # Amber and Coral stay level after (d) and (e), so (f) the name decides: Coral's
        # win over Amber does not count again.
        matches = m("A-D 1-0, D-C 1-0, D-B 0-0, B-C 1-1, A-B 1-1, A-C 0-1")
        self.assertEqual(standings(matches), names("ACDB"))

    def test_teams_that_never_met(self):
        # Blue, Coral and Dune have 6 points. Coral and Dune never played each other: after
        # Blue is separated, their own mini-table is empty (all zeros), so step 3 applies.
        matches = m("B-C 1-0, B-D 1-0, C-E 3-0, C-F 1-0, D-E 4-0, D-F 1-0, E-F 0-0")
        self.assertEqual(standings(matches), names("BDCFE"))


if __name__ == "__main__":
    unittest.main()
