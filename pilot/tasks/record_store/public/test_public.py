"""Public checks for records.py.

Usage (with records.py importable, e.g. in the task sandbox):
    python -m pytest public/test_public.py
"""

import pytest
from records import RecordStore, ValidationError

ADA = {"name": "Ada", "email": "ada@example.com", "age": 36}


def test_add_then_get(tmp_path):
    store = RecordStore(tmp_path / "db")
    record_id = store.add(ADA)
    assert store.get(record_id) == ADA


def test_invalid_email_is_rejected(tmp_path):
    store = RecordStore(tmp_path / "db")
    with pytest.raises(ValidationError):
        store.add({**ADA, "email": "not-an-email"})


def test_records_survive_reopening(tmp_path):
    record_id = RecordStore(tmp_path / "db").add(ADA)
    assert RecordStore(tmp_path / "db").get(record_id) == ADA
