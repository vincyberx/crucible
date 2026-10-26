"""LRU cache with a per-entry time-to-live. Reference implementation."""

import time
from collections import OrderedDict


class TTLCache:
    def __init__(self, capacity, ttl, clock=time.monotonic):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 0:
            raise ValueError("capacity must be an integer >= 0")
        if not ttl > 0:
            raise ValueError("ttl must be > 0")
        self.capacity = capacity
        self.ttl = ttl
        self.clock = clock
        self._data = OrderedDict()  # key -> (value, expires_at); order = LRU -> MRU

    def _purge(self, now):
        dead = [k for k, (_, exp) in self._data.items() if now >= exp]
        for k in dead:
            del self._data[k]

    def get(self, key, default=None):
        now = self.clock()
        self._purge(now)
        if key not in self._data:
            return default
        self._data.move_to_end(key)
        return self._data[key][0]

    def put(self, key, value):
        now = self.clock()
        self._purge(now)
        if self.capacity == 0:
            return
        if key in self._data:
            self._data[key] = (value, now + self.ttl)
            self._data.move_to_end(key)
            return
        self._data[key] = (value, now + self.ttl)
        while len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def __contains__(self, key):
        now = self.clock()
        item = self._data.get(key)
        return item is not None and now < item[1]

    def __len__(self):
        now = self.clock()
        return sum(1 for _, exp in self._data.values() if now < exp)

    def keys(self):
        now = self.clock()
        return [k for k, (_, exp) in self._data.items() if now < exp]
