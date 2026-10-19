"""File-backed record store with validation and JSON persistence.

Correct solution for record_store before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from records import RecordStore, ValidationError
    store = RecordStore("records.json")
    record_id = store.add({"name": "Ada", "email": "ada@example.com", "age": 36})
"""

import json
import os
from pathlib import Path

FIELDS = ("name", "email", "age")


class ValidationError(Exception):
    pass


def validate(record):
    if not isinstance(record, dict) or set(record) != set(FIELDS):
        raise ValidationError(f"a record must be a dict with exactly the keys {FIELDS}")
    name, email, age = record["name"], record["email"], record["age"]
    if not isinstance(name, str) or not 1 <= len(name) <= 100:
        raise ValidationError("name must be a string of 1 to 100 characters")
    if not isinstance(email, str) or "@" not in email:
        raise ValidationError("email must contain an @")
    if isinstance(age, bool) or not isinstance(age, int) or not 0 <= age <= 150:
        raise ValidationError("age must be an integer from 0 to 150")


def check_fields(fields):
    if not isinstance(fields, dict) or not fields or not set(fields) <= set(FIELDS):
        raise ValidationError(f"fields must be a non-empty dict with keys from {FIELDS}")


class RecordStore:
    def __init__(self, path):
        self._path = Path(path)
        self._records = {}
        self._next_id = 1
        if self._path.exists():
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._records = {int(k): v for k, v in data["records"].items()}
            self._next_id = data["next_id"]

    def add(self, record):
        validate(record)
        record_id = self._next_id
        self._commit({**self._records, record_id: dict(record)}, record_id + 1)
        return record_id

    def get(self, record_id):
        return dict(self._lookup(record_id))

    def update(self, record_id, fields):
        current = self._lookup(record_id)
        check_fields(fields)
        merged = {**current, **fields}
        validate(merged)
        self._commit({**self._records, record_id: merged}, self._next_id)

    def delete(self, record_id):
        self._lookup(record_id)
        records = dict(self._records)
        del records[record_id]
        self._commit(records, self._next_id)

    def list_ids(self):
        return sorted(self._records)

    def _lookup(self, record_id):
        # True == 1 and 1.0 == 1 in Python, so a plain dict lookup would find
        # record 1 for them; treating every non-int as "not stored" is simplest.
        if isinstance(record_id, bool) or not isinstance(record_id, int):
            raise KeyError(record_id)
        if record_id not in self._records:
            raise KeyError(record_id)
        return self._records[record_id]

    def _commit(self, records, next_id):
        # Write the new state first and only then adopt it in memory, so a
        # failed write leaves the store unchanged. os.replace is atomic, so
        # the file is never half-written.
        payload = {"next_id": next_id, "records": {str(k): v for k, v in records.items()}}
        tmp = self._path.with_name(self._path.name + ".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(tmp, self._path)
        self._records, self._next_id = records, next_id
