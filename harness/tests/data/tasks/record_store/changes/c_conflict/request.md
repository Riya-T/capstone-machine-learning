Add optimistic concurrency control to `records.py`.

- Every record has a version number. A record's version is 1 when it is
  added and goes up by 1 with each successful `update`.
- Add `RecordStore.get_version(record_id) -> int`. It raises `KeyError` for an
  id that is not stored.
- Add a keyword argument `expected_version=None` to `update` and `delete`. When
  it is not `None` and differs from the record's current version, raise
  `ConflictError` and change nothing. `expected_version` is an `int` or `None`;
  other values are unspecified.
- Checks happen in this order: an id that is not stored raises `KeyError`
  first, then a version mismatch raises `ConflictError`, and only then is
  `fields` checked.
- Add `class ConflictError(Exception)` to `records.py`. It is not a subclass
  of `ValidationError`.
- Versions are saved to the file and survive reopening the store.

All existing behavior must keep working.
