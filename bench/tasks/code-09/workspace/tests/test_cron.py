import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cron import next_fire  # noqa: E402


class TestNextFireBasics(unittest.TestCase):
    def test_every_quarter_hour(self):
        self.assertEqual(next_fire("*/15 * * * *", datetime(2026, 3, 10, 10, 7)),
                         datetime(2026, 3, 10, 10, 15))

    def test_daily_later_same_day(self):
        self.assertEqual(next_fire("0 9 * * *", datetime(2026, 3, 10, 8, 30)),
                         datetime(2026, 3, 10, 9, 0))

    def test_monthly(self):
        self.assertEqual(next_fire("30 18 1 * *", datetime(2026, 1, 15, 12, 0)),
                         datetime(2026, 2, 1, 18, 30))

    def test_yearly(self):
        self.assertEqual(next_fire("0 0 1 1 *", datetime(2026, 6, 1)),
                         datetime(2027, 1, 1, 0, 0))

    def test_list_and_range(self):
        self.assertEqual(next_fire("5,10-12 * * * *", datetime(2026, 3, 10, 10, 6)),
                         datetime(2026, 3, 10, 10, 10))

    def test_rolls_over_midnight(self):
        self.assertEqual(next_fire("0 * * * *", datetime(2026, 3, 10, 23, 30)),
                         datetime(2026, 3, 11, 0, 0))

    def test_invalid(self):
        for bad in ["* * * *", "60 * * * *"]:
            with self.assertRaises(ValueError, msg=bad):
                next_fire(bad, datetime(2026, 1, 1))


if __name__ == "__main__":
    unittest.main()
