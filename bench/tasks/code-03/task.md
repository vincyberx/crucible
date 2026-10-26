# Task: an LRU cache with time-to-live, exact semantics

The current directory is a small Python 3 project (standard library only).
`ttlcache.py` contains a class `TTLCache` that combines a capacity limit (least recently
used eviction) with a per-entry time-to-live. The current implementation has several bugs.
Fix it so that it follows the specification below exactly.

Modify the files in the current directory so that every requirement below is met.
The deliverable is the code in place. You may add tests; do not delete the existing ones.
The existing tests run with `python3 -m unittest discover -s tests -q` from this directory.

## Specification of `TTLCache(capacity, ttl, clock=time.monotonic)`

- `capacity` is the maximum number of **live** entries; it must be an integer `>= 0`.
  `ttl` is a number of seconds and must be `> 0`. Otherwise the constructor raises `ValueError`.
- `clock` is a zero-argument callable returning the current time in seconds (tests inject a
  fake clock). Read the time from `clock()` on every operation.
- Keys are hashable; values may be any object, **including `None`**.

**Lifetime.** An entry written by `put` at time `t` is *live* while `clock() < t + ttl`.
At `clock() >= t + ttl` it is *expired*. Expired entries are invisible: `get` returns the
default, `in` is `False`, they are not counted by `len()` and not listed by `keys()`.

**Methods.**
1. `get(key, default=None)`: if `key` is live, return its value and make it the most
   recently used entry. Reading does **not** extend its lifetime. Otherwise return `default`.
2. `put(key, value)`:
   - if `key` is live: replace the value, restart its lifetime from now, and make it the most
     recently used entry. Nothing is evicted.
   - otherwise (absent or expired): insert it as the most recently used entry. If the number
     of live entries would then exceed `capacity`, evict the least recently used **live**
     entry. Expired entries never count toward the capacity and must never cause a live
     entry to be evicted.
   - with `capacity == 0`, `put` stores nothing.
3. `key in cache`: `True` iff `key` is live. It does not change recency.
4. `len(cache)`: number of live entries. It does not change recency.
5. `keys()`: list of live keys ordered from least recently used to most recently used.
   It does not change recency.

"Recency" is changed only by a successful `get` and by `put`.
