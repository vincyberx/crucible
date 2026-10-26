import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ttlcache import TTLCache  # noqa: E402


class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t


def make(capacity, ttl):
    clock = FakeClock()
    return TTLCache(capacity, ttl, clock=clock), clock


class TestLifetime(unittest.TestCase):
    def test_expiry_boundary_is_exclusive(self):
        c, clock = make(3, 10)
        c.put("a", 1)
        clock.t = 9.999
        self.assertEqual(c.get("a"), 1)
        clock.t = 10
        self.assertIsNone(c.get("a"))
        self.assertNotIn("a", c)

    def test_contains_at_boundary(self):
        c, clock = make(3, 10)
        c.put("a", 1)
        clock.t = 10
        self.assertFalse("a" in c)
        self.assertEqual(len(c), 0)
        self.assertEqual(c.keys(), [])

    def test_get_does_not_extend_lifetime(self):
        c, clock = make(3, 10)
        c.put("a", 1)
        clock.t = 9
        self.assertEqual(c.get("a"), 1)
        clock.t = 10
        self.assertIsNone(c.get("a"))

    def test_put_existing_restarts_lifetime(self):
        c, clock = make(3, 10)
        c.put("a", 1)
        clock.t = 5
        c.put("a", 2)
        clock.t = 14.5
        self.assertEqual(c.get("a"), 2)
        clock.t = 15
        self.assertIsNone(c.get("a"))

    def test_len_and_keys_count_live_only(self):
        c, clock = make(5, 10)
        c.put("a", 1)
        clock.t = 4
        c.put("b", 2)
        clock.t = 11
        self.assertEqual(len(c), 1)
        self.assertEqual(c.keys(), ["b"])

    def test_reput_expired_key_is_new_entry(self):
        c, clock = make(3, 10)
        c.put("a", 1)
        c.put("b", 2)
        clock.t = 10
        c.put("a", 3)
        self.assertEqual(c.keys(), ["a"])
        self.assertEqual(c.get("a"), 3)


class TestRecency(unittest.TestCase):
    def test_contains_does_not_touch_recency(self):
        c, _ = make(2, 100)
        c.put("a", 1)
        c.put("b", 2)
        self.assertTrue("a" in c)
        c.put("c", 3)
        self.assertEqual(c.keys(), ["b", "c"])

    def test_len_and_keys_do_not_touch_recency(self):
        c, _ = make(2, 100)
        c.put("a", 1)
        c.put("b", 2)
        len(c)
        c.keys()
        c.put("c", 3)
        self.assertEqual(c.keys(), ["b", "c"])

    def test_none_value_is_present(self):
        c, _ = make(2, 100)
        c.put("k", None)
        self.assertTrue("k" in c)
        self.assertEqual(len(c), 1)
        self.assertEqual(c.get("k", "dflt"), None)

    def test_put_existing_when_full_no_eviction(self):
        c, _ = make(2, 100)
        c.put("a", 1)
        c.put("b", 2)
        c.put("a", 10)
        self.assertEqual(c.keys(), ["b", "a"])
        self.assertEqual(c.get("b"), 2)
        self.assertEqual(c.get("a"), 10)

    def test_get_refreshes_recency(self):
        c, _ = make(3, 100)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        c.get("a")
        self.assertEqual(c.keys(), ["b", "c", "a"])
        c.put("d", 4)
        self.assertEqual(c.keys(), ["c", "a", "d"])

    def test_failed_get_on_missing_key_changes_nothing(self):
        c, _ = make(2, 100)
        c.put("a", 1)
        c.put("b", 2)
        self.assertIsNone(c.get("zzz"))
        c.put("c", 3)
        self.assertEqual(c.keys(), ["b", "c"])


class TestCapacityAndExpiry(unittest.TestCase):
    def test_expired_entry_does_not_cause_live_eviction(self):
        c, clock = make(2, 10)
        c.put("a", 1)          # expires at 10
        clock.t = 1
        c.put("b", 2)          # expires at 11
        clock.t = 2
        c.get("a")             # a is now MRU, b is LRU
        clock.t = 10.5         # a expired, b live
        c.put("c", 3)
        self.assertEqual(c.get("b"), 2)
        self.assertEqual(c.get("c"), 3)
        self.assertEqual(len(c), 2)

    def test_several_expired_do_not_count(self):
        c, clock = make(3, 10)
        c.put("x", 0)          # expires 10
        clock.t = 5
        c.put("a", 1)          # expires 15
        c.put("b", 2)          # expires 15
        clock.t = 6
        c.get("x")             # recency: a, b, x
        clock.t = 12           # x expired
        c.put("c", 3)
        c.put("d", 4)          # now live a, b, c, d -> evict a (LRU live)
        self.assertEqual(c.keys(), ["b", "c", "d"])

    def test_capacity_zero(self):
        c, _ = make(0, 10)
        c.put("a", 1)
        self.assertIsNone(c.get("a"))
        self.assertEqual(len(c), 0)
        self.assertEqual(c.keys(), [])

    def test_capacity_one(self):
        c, _ = make(1, 10)
        c.put("a", 1)
        c.put("b", 2)
        self.assertEqual(c.keys(), ["b"])


class TestValidation(unittest.TestCase):
    def test_negative_capacity(self):
        with self.assertRaises(ValueError):
            TTLCache(-1, 10, clock=FakeClock())

    def test_zero_ttl(self):
        with self.assertRaises(ValueError):
            TTLCache(2, 0, clock=FakeClock())

    def test_negative_ttl(self):
        with self.assertRaises(ValueError):
            TTLCache(2, -5, clock=FakeClock())


if __name__ == "__main__":
    unittest.main()
