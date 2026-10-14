# Record store

Write a module `records.py` that stores person records in a file and checks
them before saving.

## Interface

```python
class ValidationError(Exception): ...


class RecordStore:
    def __init__(self, path): ...
    def add(self, record: dict) -> int: ...
    def get(self, record_id: int) -> dict: ...
    def update(self, record_id: int, fields: dict) -> None: ...
    def delete(self, record_id: int) -> None: ...
    def list_ids(self) -> list[int]: ...
```

`path` is a `str` or `pathlib.Path` naming the storage file.

## Records

A record is a `dict` with exactly the keys `name`, `email` and `age`:

- `name`: a `str` of 1 to 100 characters.
- `email`: a `str` containing exactly one `@`, with at least one character
  before and after it.
- `age`: an `int` from 0 to 150 inclusive. `bool` values are not accepted.

Anything else, including a missing or extra key or a value that is not a
`dict`, raises `ValidationError`. Two records may have the same email.

## Operations

- `add(record)` validates the record, stores a copy, and returns its id. Ids
  are integers that start at 1 and increase by 1 with each successful `add`.
  An id is never reused, even after its record is deleted.
- `get(record_id)` returns a copy of the record (the three fields only).
  Changing the returned dict does not change the store.
- `update(record_id, fields)` changes some of a record's fields. `fields`
  must be a non-empty `dict` whose keys are a subset of `name`, `email` and
  `age`; otherwise `update` raises `ValidationError`. The record after the
  update must be valid.
- `delete(record_id)` removes the record.
- `list_ids()` returns the ids of all stored records in increasing order.

`get`, `update` and `delete` raise `KeyError` for an id that is not stored.
Ids are `int` values; any other value, including `True` or `1.0`, is an id
that is not stored. If the id is not stored, `KeyError` is raised before
`fields` is checked.

A failed operation has no effect: if `add`, `update` or `delete` raises, the
store, the file, and the id that the next `add` will return are all unchanged.

## Persistence

Every successful `add`, `update` and `delete` is saved to the file before the
method returns. A new `RecordStore` created with the same path sees exactly the
saved records and continues the id sequence. If the file does not exist, the
store starts empty. The file format is up to you.

Creating a `RecordStore` reads the file as it is at that moment. Once one
store has changed the file, what an older store for the same path does is
unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes a file that is corrupt or was not written by this module, a path
that is a directory or cannot be written, and several stores changing the
same file.
