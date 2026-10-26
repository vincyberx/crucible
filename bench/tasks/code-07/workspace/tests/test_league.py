import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from league import standings  # noqa: E402


class TestStandings(unittest.TestCase):
    def test_no_ties(self):
        matches = [
            ("Amber", "Blue", 2, 0),
            ("Blue", "Coral", 1, 0),
            ("Amber", "Coral", 3, 1),
        ]
        self.assertEqual(standings(matches), ["Amber", "Blue", "Coral"])

    def test_head_to_head_beats_overall_goal_difference(self):
        matches = [
            ("Amber", "Coral", 4, 0),
            ("Amber", "Dune", 3, 0),
            ("Blue", "Amber", 1, 0),
            ("Blue", "Dune", 1, 0),
            ("Coral", "Blue", 1, 0),
            ("Coral", "Dune", 0, 0),
        ]
        # Amber and Blue both have 6 points; Blue won the match between them.
        self.assertEqual(standings(matches), ["Blue", "Amber", "Coral", "Dune"])

    def test_drawn_head_to_head_goes_to_goal_difference(self):
        matches = [
            ("Amber", "Blue", 1, 1),
            ("Amber", "Coral", 1, 0),
            ("Blue", "Coral", 3, 0),
        ]
        self.assertEqual(standings(matches), ["Blue", "Amber", "Coral"])

    def test_everything_equal_falls_back_to_name(self):
        self.assertEqual(standings([("Zinc", "Amber", 0, 0)]), ["Amber", "Zinc"])

    def test_three_teams_separated_by_mini_table(self):
        matches = [
            ("Amber", "Blue", 3, 0),
            ("Blue", "Coral", 2, 0),
            ("Coral", "Amber", 1, 0),
            ("Dune", "Coral", 0, 5),
            ("Dune", "Blue", 0, 1),
            ("Dune", "Amber", 0, 1),
        ]
        # Amber, Blue and Coral have 6 points each. Among the three: Amber +2,
        # Blue -1 (2 scored), Coral -1 (1 scored).
        self.assertEqual(standings(matches), ["Amber", "Blue", "Coral", "Dune"])


if __name__ == "__main__":
    unittest.main()
