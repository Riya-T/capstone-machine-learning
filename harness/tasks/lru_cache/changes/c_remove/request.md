Add ways to take entries out of `cache.py` by hand.

- Add `Cache.remove(key) -> int`, which removes the entry and returns the
  value it held. It raises `KeyError` for a key that is not cached,
  including non-str values, and then nothing changes.
- Add `Cache.clear_prefix(prefix) -> list[str]`, which removes every entry
  whose key starts with `prefix` and returns the removed keys, most recently
  used first. `prefix` must be a `str`, or `ValueError` is raised and
  nothing changes; the empty prefix matches every key. When no key matches,
  nothing is removed and `[]` is returned.
- After an entry is removed, its key is missing for `get`, the size goes
  down by one, and the key may be put again later as a new entry.
- Removing entries does not change the order of the remaining ones.

All existing behavior must keep working.
