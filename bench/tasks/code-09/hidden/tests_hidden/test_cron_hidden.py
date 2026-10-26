import os
import sys
import time
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cron import next_fire  # noqa: E402

D = datetime
MON = D(2026, 10, 26)  # a Monday, 00:00


class TestDayRule(unittest.TestCase):
    def test_both_restricted_means_or(self):
        # Fridays or the 13th.
        self.assertEqual(next_fire("0 12 13 * 5", MON), D(2026, 10, 30, 12, 0))
        self.assertEqual(next_fire("0 12 13 * 5", D(2026, 12, 11, 12, 0)),  # a Friday
                         D(2026, 12, 13, 12, 0))  # a Sunday

    def test_dow_star_means_and(self):
        self.assertEqual(next_fire("0 0 13 * *", MON), D(2026, 11, 13, 0, 0))

    def test_dom_star_means_and(self):
        self.assertEqual(next_fire("0 0 * * 3", MON), D(2026, 10, 28, 0, 0))

    def test_field_starting_with_star_is_unrestricted(self):
        # "*/2" starts with '*': unrestricted, so AND: an odd day that is a Monday.
        self.assertEqual(next_fire("0 0 */2 * 1", MON), D(2026, 11, 9, 0, 0))
        # "*/1" starts with '*': AND with the 13th.
        self.assertEqual(next_fire("0 0 13 * */1", MON), D(2026, 11, 13, 0, 0))
        # "*/7" is {0, 7}, Sunday, and starts with '*': 29 February that is a Sunday.
        self.assertEqual(next_fire("0 0 29 2 */7", D(2026, 1, 1)), D(2032, 2, 29, 0, 0))

    def test_field_not_starting_with_star_is_restricted(self):
        # "1-31/2" lists the same days as "*/2" but starts with a digit: OR.
        self.assertEqual(next_fire("0 0 1-31/2 * 1", MON), D(2026, 10, 27, 0, 0))

    def test_or_rescues_an_impossible_day_of_month(self):
        # 30 February never exists, but Mondays in February do.
        self.assertEqual(next_fire("0 0 30 2 1", D(2026, 3, 1)), D(2027, 2, 1, 0, 0))


class TestWeekdays(unittest.TestCase):
    def test_sunday_is_0_and_7(self):
        self.assertEqual(next_fire("0 0 * * 0", MON), D(2026, 11, 1, 0, 0))
        self.assertEqual(next_fire("0 0 * * 7", MON), D(2026, 11, 1, 0, 0))

    def test_monday_is_1(self):
        self.assertEqual(next_fire("0 0 * * 1", MON), D(2026, 11, 2, 0, 0))

    def test_range_up_to_7(self):
        self.assertEqual(next_fire("0 0 * * 5-7", MON), D(2026, 10, 30, 0, 0))
        self.assertEqual(next_fire("0 0 * * 5-7", D(2026, 10, 31)), D(2026, 11, 1, 0, 0))


class TestSteps(unittest.TestCase):
    def test_star_step_starts_at_field_minimum(self):
        self.assertEqual(next_fire("0 0 */10 * *", D(2026, 1, 1)), D(2026, 1, 11, 0, 0))
        self.assertEqual(next_fire("0 0 1 */5 *", D(2026, 1, 1)), D(2026, 6, 1, 0, 0))

    def test_range_step(self):
        self.assertEqual(next_fire("5-20/7 * * * *", D(2026, 1, 1, 10, 12)),
                         D(2026, 1, 1, 10, 19))
        self.assertEqual(next_fire("5-20/7 * * * *", D(2026, 1, 1, 10, 19)),
                         D(2026, 1, 1, 11, 5))


class TestStrictlyLater(unittest.TestCase):
    def test_exact_match_is_skipped(self):
        self.assertEqual(next_fire("* * * * *", D(2026, 1, 1, 10, 0, 0)), D(2026, 1, 1, 10, 1))
        self.assertEqual(next_fire("0 9 * * *", D(2026, 1, 1, 9, 0)), D(2026, 1, 2, 9, 0))

    def test_seconds_are_dropped(self):
        self.assertEqual(next_fire("* * * * *", D(2026, 1, 1, 10, 0, 30)), D(2026, 1, 1, 10, 1))
        self.assertEqual(next_fire("0 9 * * *", D(2026, 1, 1, 8, 59, 59, 999999)),
                         D(2026, 1, 1, 9, 0))


class TestCalendar(unittest.TestCase):
    def test_skips_short_months(self):
        self.assertEqual(next_fire("0 0 31 * *", D(2026, 1, 31)), D(2026, 3, 31, 0, 0))

    def test_leap_day(self):
        self.assertEqual(next_fire("0 0 29 2 *", D(2026, 3, 1)), D(2028, 2, 29, 0, 0))

    def test_2100_is_not_a_leap_year(self):
        self.assertEqual(next_fire("0 0 29 2 *", D(2096, 3, 1)), D(2104, 2, 29, 0, 0))

    def test_impossible_dates_return_none_quickly(self):
        start = time.monotonic()
        self.assertIsNone(next_fire("0 0 30 2 *", D(2026, 1, 1)))
        self.assertIsNone(next_fire("0 0 31 4,6,9,11 *", D(2026, 1, 1)))
        self.assertLess(time.monotonic() - start, 5.0)


class TestValidation(unittest.TestCase):
    def test_invalid_expressions(self):
        for bad in ["* * * * * *", "* * * * 8", "* * 0 * *", "* * 32 * *", "* * * 13 *",
                    "* 24 * * *", "*/0 * * * *", "5/15 * * * *", "3-1 * * * *",
                    "1,,2 * * * *", "* * * * MON", "-1 * * * *", "1-2-3 * * * *"]:
            with self.assertRaises(ValueError, msg=bad):
                next_fire(bad, D(2026, 1, 1))

    def test_seven_is_a_valid_day_of_week(self):
        self.assertIsNotNone(next_fire("0 0 * * 7", D(2026, 1, 1)))


if __name__ == "__main__":
    unittest.main()
