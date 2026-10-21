"""LRU cache whose entries can also be removed by hand, singly or by key prefix.

Correct solution for lru_cache after c_remove.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from cache import Cache
    cache = Cache(2)
    cache.put("user:1", 1)
    cache.clear_prefix("user:")  # -> ["user:1"]
"""


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

    def put(self, key, value):
        check_key(key)
        check_value(value)
        if key in self._entries:
            del self._entries[key]
        elif len(self._entries) >= self._capacity:
            self._evict()
        self._entries[key] = value

    def get(self, key):
        self._require(key)
        value = self._entries.pop(key)
        self._entries[key] = value  # back in as the most recently used
        return value

    def remove(self, key):
        self._require(key)
        return self._entries.pop(key)

    def clear_prefix(self, prefix):
        if not isinstance(prefix, str):
            raise ValueError(f"prefix must be a str, got {prefix!r}")
        removed = [key for key in self.get_keys() if key.startswith(prefix)]
        for key in removed:
            del self._entries[key]
        return removed

    def get_keys(self):
        return list(reversed(self._entries))

    def get_size(self):
        return len(self._entries)

    def get_capacity(self):
        return self._capacity

    def _evict(self):
        oldest = next(iter(self._entries))
        del self._entries[oldest]

    def _require(self, key):
        # Non-str keys are never stored, so they count as missing too.
        if not isinstance(key, str) or key not in self._entries:
            raise KeyError(key)
