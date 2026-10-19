"""File-backed record store with validation, JSON persistence, optimistic
concurrency control and transactions.

Correct solution for record_store after c_conflict and c_txn.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from records import RecordStore, ValidationError
    store = RecordStore("records.json")
    record_id = store.add({"name": "Ada", "email": "ada@example.com", "age": 36})
"""

import json
import os
from contextlib import contextmanager
from pathlib import Path

FIELDS = ("name", "email", "age")


class ValidationError(Exception):
    pass


class ConflictError(Exception):
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
        self._versions = {}
        self._next_id = 1
        self._in_transaction = False
        if self._path.exists():
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._records = {int(k): v for k, v in data["records"].items()}
            self._versions = {int(k): v for k, v in data["versions"].items()}
            self._next_id = data["next_id"]

    def add(self, record):
        validate(record)
        record_id = self._next_id
        self._commit(
            {**self._records, record_id: dict(record)},
            {**self._versions, record_id: 1},
            record_id + 1,
        )
        return record_id

    def get(self, record_id):
        return dict(self._lookup(record_id))

    def get_version(self, record_id):
        self._lookup(record_id)
        return self._versions[record_id]

    def update(self, record_id, fields, expected_version=None):
        current = self._lookup(record_id)
        self._check_version(record_id, expected_version)
        check_fields(fields)
        merged = {**current, **fields}
        validate(merged)
        self._commit(
            {**self._records, record_id: merged},
            {**self._versions, record_id: self._versions[record_id] + 1},
            self._next_id,
        )

    def delete(self, record_id, expected_version=None):
        self._lookup(record_id)
        self._check_version(record_id, expected_version)
        records = dict(self._records)
        versions = dict(self._versions)
        del records[record_id], versions[record_id]
        self._commit(records, versions, self._next_id)

    def list_ids(self):
        return sorted(self._records)

    @contextmanager
    def transaction(self):
        if self._in_transaction:
            raise RuntimeError("transactions cannot be nested")
        # Every operation replaces the state dicts instead of mutating them,
        # so keeping references to the current ones is a complete snapshot.
        snapshot = (self._records, self._versions, self._next_id)
        self._in_transaction = True
        try:
            yield
            self._write(self._records, self._versions, self._next_id)
        except BaseException:
            self._records, self._versions, self._next_id = snapshot
            raise
        finally:
            self._in_transaction = False

    def _lookup(self, record_id):
        # True == 1 and 1.0 == 1 in Python, so a plain dict lookup would find
        # record 1 for them; treating every non-int as "not stored" is simplest.
        if isinstance(record_id, bool) or not isinstance(record_id, int):
            raise KeyError(record_id)
        if record_id not in self._records:
            raise KeyError(record_id)
        return self._records[record_id]

    def _check_version(self, record_id, expected_version):
        if expected_version is not None and expected_version != self._versions[record_id]:
            raise ConflictError(
                f"record {record_id} is at version {self._versions[record_id]}, "
                f"not {expected_version}"
            )

    def _commit(self, records, versions, next_id):
        # Inside a transaction, changes stay in memory until the block exits.
        if not self._in_transaction:
            self._write(records, versions, next_id)
        self._records, self._versions, self._next_id = records, versions, next_id

    def _write(self, records, versions, next_id):
        # os.replace is atomic, so the file is never half-written.
        payload = {
            "next_id": next_id,
            "records": {str(k): v for k, v in records.items()},
            "versions": {str(k): v for k, v in versions.items()},
        }
        tmp = self._path.with_name(self._path.name + ".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(tmp, self._path)
