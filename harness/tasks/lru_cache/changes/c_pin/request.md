Let entries in `cache.py` be pinned, so they are never dropped.

- Add `class CacheFull(Exception)` to `cache.py`.
- Add `Cache.pin(key)`, `Cache.unpin(key)` and `Cache.is_pinned(key) -> bool`.
  All three raise `KeyError` for a key that is not cached, including
  non-str values. New entries are not pinned. Pinning a pinned key, or
  unpinning one that is not pinned, does nothing. None of the three changes
  which key is the most recently used.
- A pinned entry is never dropped to make room. When `put` of a new key
  needs room, it drops the least recently used entry among the entries
  that are not pinned. When every entry is pinned and the cache is full,
  `put` of a new key raises `CacheFull` and changes nothing.
- `put` of a key that is already cached always works, whether or not the
  cache is full, and the key stays pinned if it was.
- Pinned entries still appear in `get_keys` in their usual position, and
  `get` and `put` on them work as before.

Error order for `put`: `ValueError` for a bad key or value, then
`CacheFull`. All existing behavior must keep working.
