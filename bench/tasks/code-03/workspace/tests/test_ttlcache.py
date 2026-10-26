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


class TestTTLCacheBasics(unittest.TestCase):
    def test_put_get(self):
        c = TTLCache(3, 10, clock=FakeClock())
        c.put("a", 1)
        self.assertEqual(c.get("a"), 1)

    def test_missing_returns_default(self):
        c = TTLCache(3, 10, clock=FakeClock())
        self.assertIsNone(c.get("nope"))
        self.assertEqual(c.get("nope", 42), 42)

    def test_lru_eviction(self):
        c = TTLCache(2, 100, clock=FakeClock())
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")
        c.put("c", 3)
        self.assertEqual(c.keys(), ["a", "c"])
        self.assertIsNone(c.get("b"))

    def test_expiry_long_after(self):
        clock = FakeClock()
        c = TTLCache(2, 10, clock=clock)
        c.put("a", 1)
        clock.t = 100
        self.assertIsNone(c.get("a"))


if __name__ == "__main__":
    unittest.main()
