"""LRU cache with statistics and pinned entries that are never dropped.

Correct solution for lru_cache after c_stats and c_pin.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from cache import Cache
    cache = Cache(2)
    cache.put("a", 1)
    cache.pin("a")
    cache.get_stats()  # -> (0, 0, 0)
"""


class CacheFull(Exception):
    pass


def check_key(key):
    if not isinstance(key, str) or not key:
        raise ValueError(f"key must be a non-empty str, got {key!r}")


def check_value(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"value must be an int, got {value!r}")


class Cache:
    def __init__(self, capacity):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
            raise ValueError(f"capacity must be a positive int, got {capacity!r}")
        self._capacity = capacity
        self._entries = {}  # key -> value, least recently used first
        self._hit_counts = {}  # key -> hits since the key entered the cache
        self._pinned = set()
        self._hits = 0
        self._misses = 0
        self._evicted = []  # keys evicted, oldest first

    def put(self, key, value):
        check_key(key)
        check_value(value)
        if key in self._entries:
            del self._entries[key]
        else:
            if len(self._entries) >= self._capacity:
                self._evict()
            self._hit_counts[key] = 0
        self._entries[key] = value

    def get(self, key):
        if not self._has(key):
            self._misses += 1
            raise KeyError(key)
        value = self._entries.pop(key)
        self._entries[key] = value  # back in as the most recently used
        self._hits += 1
        self._hit_counts[key] += 1
        return value

    def pin(self, key):
        self._require(key)
        self._pinned.add(key)

    def unpin(self, key):
        self._require(key)
        self._pinned.discard(key)

    def is_pinned(self, key):
        self._require(key)
        return key in self._pinned

    def get_keys(self):
        return list(reversed(self._entries))

    def get_size(self):
        return len(self._entries)

    def get_capacity(self):
        return self._capacity

    def get_stats(self):
        return (self._hits, self._misses, len(self._evicted))

    def get_evicted(self):
        return list(self._evicted)

    def get_hit_count(self, key):
        self._require(key)
        return self._hit_counts[key]

    def _evict(self):
        for key in self._entries:  # least recently used first
            if key not in self._pinned:
                del self._entries[key]
                del self._hit_counts[key]
                self._evicted.append(key)
                return
        raise CacheFull("every entry is pinned")

    def _has(self, key):
        # Non-str keys are never stored, so they count as missing too.
        return isinstance(key, str) and key in self._entries

    def _require(self, key):
        if not self._has(key):
            raise KeyError(key)
