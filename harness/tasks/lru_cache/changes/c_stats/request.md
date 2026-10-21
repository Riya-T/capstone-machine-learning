Add usage statistics to `cache.py`.

- Add `Cache.get_stats() -> tuple[int, int, int]`, returning
  `(hits, misses, evictions)` counted since the cache was created. A `get`
  that returns a value is a hit; a `get` that raises `KeyError` is a miss.
  An eviction is an entry dropped by `put` to make room for a new key.
  Nothing else changes these counts: replacing the value of a cached key is
  not an eviction, and neither is any other way an entry may leave the
  cache.
- Add `Cache.get_evicted() -> list[str]`: the keys evicted so far, oldest
  eviction first. A key evicted more than once appears once per eviction.
- Add `Cache.get_hit_count(key) -> int`: the number of hits on that key
  since it last entered the cache. Replacing its value keeps the count; an
  entry that left the cache and is put again starts at 0. It raises
  `KeyError` for a key that is not cached, including non-str values, and
  that does not count as a miss. Calling it does not change which key is
  the most recently used.

All existing behavior must keep working.
