# LRU cache

Write a module `cache.py` with a cache that holds at most a fixed number of
`int` values under string keys. When it is full and a new key is put in,
the entry that was used least recently is dropped to make room.

## Interface

```python
class Cache:
    def __init__(self, capacity: int): ...
    def put(self, key: str, value: int) -> None: ...
    def get(self, key: str) -> int: ...
    def get_keys(self) -> list[str]: ...
    def get_size(self) -> int: ...
    def get_capacity(self) -> int: ...
```

## Capacity

- `Cache(capacity)` makes an empty cache that can hold `capacity` entries.
  `capacity` must be an `int` greater than 0, or `ValueError` is raised.
- `get_capacity()` returns that number. `get_size()` returns the number of
  entries in the cache right now, which is never more than the capacity.

## Putting and getting

- `put(key, value)` stores the value under the key. `key` must be a
  non-empty `str` and `value` an `int`, or `ValueError` is raised. When the
  key is already in the cache, its value is replaced and the size does not
  change. When the key is new and the cache is full, the least recently
  used entry is dropped first.
- `get(key)` returns the value stored under the key. A key that is not in
  the cache raises `KeyError`, including values that are not strings at
  all, such as `None` or `1`.
- Using a key means calling `put` or `get` with it. Every successful `put`
  or `get` makes its key the most recently used one. The least recently
  used entry is the one whose key was used longest ago.
- `get_keys()` returns the keys in the cache, most recently used first.

A failed call has no effect: if a method raises, the entries and their
order are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` values passed as capacity or value, what happens if a
returned list is changed, the text of error messages, saving the cache to a
file, and use from several threads.
