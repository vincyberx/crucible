"""LRU cache with a per-entry time-to-live."""

import time
from collections import OrderedDict


class TTLCache:
    def __init__(self, capacity, ttl, clock=time.monotonic):
        self.capacity = capacity
        self.ttl = ttl
        self.clock = clock
        self._data = OrderedDict()  # key -> (value, expires_at)

    def _alive(self, key):
        item = self._data.get(key)
        return item is not None and self.clock() <= item[1]

    def get(self, key, default=None):
        if not self._alive(key):
            return default
        value, _ = self._data[key]
        self._data[key] = (value, self.clock() + self.ttl)
        self._data.move_to_end(key)
        return value

    def put(self, key, value):
        self._data[key] = (value, self.clock() + self.ttl)
        self._data.move_to_end(key)
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def __contains__(self, key):
        return self.get(key) is not None

    def __len__(self):
        return len(self._data)

    def keys(self):
        return list(self._data)
