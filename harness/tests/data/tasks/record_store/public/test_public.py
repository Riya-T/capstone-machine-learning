"""Public checks for records.py.

Usage (with records.py importable, e.g. in the sandbox):
    python -m pytest public/test_public.py
"""

import pytest
from records import RecordStore, ValidationError

ADA = {"name": "Ada", "email": "ada@example.com", "age": 36}
GRACE = {"name": "Grace", "email": "grace@example.com", "age": 45}


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


def test_a_string_age_and_an_empty_name_are_rejected(tmp_path):
    store = RecordStore(tmp_path / "db")
    with pytest.raises(ValidationError):
        store.add({**ADA, "age": "36"})
    with pytest.raises(ValidationError):
        store.add({**ADA, "name": ""})


def test_limits_themselves_are_allowed(tmp_path):
    store = RecordStore(tmp_path / "db")
    newborn = {"name": "N" * 100, "email": "n@example.com", "age": 0}
    assert store.get(store.add(newborn)) == newborn


def test_reopened_store_has_int_ids_and_keeps_counting(tmp_path):
    first_id = RecordStore(tmp_path / "db").add(ADA)
    reopened = RecordStore(tmp_path / "db")
    assert reopened.list_ids() == [first_id]
    assert type(reopened.list_ids()[0]) is int
    assert reopened.add(GRACE) == first_id + 1


def test_rejected_update_leaves_the_record_as_it_was(tmp_path):
    store = RecordStore(tmp_path / "db")
    record_id = store.add(ADA)
    with pytest.raises(ValidationError):
        store.update(record_id, {"name": "Ada L.", "age": -1})
    assert store.get(record_id) == ADA
    assert RecordStore(tmp_path / "db").get(record_id) == ADA


def test_rejected_add_changes_nothing(tmp_path):
    store = RecordStore(tmp_path / "db")
    store.add(ADA)
    with pytest.raises(ValidationError):
        store.add({**GRACE, "email": "grace"})
    assert store.list_ids() == [1]
    assert store.add(GRACE) == 2
