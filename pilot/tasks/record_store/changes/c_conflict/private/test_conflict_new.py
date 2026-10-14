"""Hidden new-feature tests for the c_conflict change. Never shown to the
writer or the editor.

Usage (with records.py importable, e.g. in the task sandbox):
    python -m pytest changes/c_conflict/private/test_conflict_new.py
"""

import pytest
from records import ConflictError, RecordStore, ValidationError

ADA = {"name": "Ada", "email": "ada@example.com", "age": 36}


@pytest.fixture
def path(tmp_path):
    return tmp_path / "db"


@pytest.fixture
def store(path):
    return RecordStore(path)


def test_each_record_has_its_own_version(store):
    first = store.add(ADA)
    second = store.add({**ADA, "email": "ada2@example.com"})
    store.update(first, {"age": 40})
    store.update(first, {"age": 41})
    assert (store.get_version(first), store.get_version(second)) == (3, 1)


def test_get_version_of_missing_id_raises_key_error(store):
    with pytest.raises(KeyError):
        store.get_version(1)


def test_matching_expected_version_allows_update(store):
    record_id = store.add(ADA)
    store.update(record_id, {"age": 37}, expected_version=1)
    assert store.get(record_id)["age"] == 37
    assert store.get_version(record_id) == 2


def test_conflicting_update_changes_nothing(store, path):
    record_id = store.add(ADA)
    with pytest.raises(ConflictError):
        store.update(record_id, {"age": 37}, expected_version=2)
    assert store.get(record_id) == ADA
    assert store.get_version(record_id) == 1
    assert RecordStore(path).get(record_id) == ADA


@pytest.mark.parametrize("fields", [{"age": -1}, {}, "junk"])
def test_version_is_checked_before_fields(store, fields):
    record_id = store.add(ADA)
    with pytest.raises(ConflictError):
        store.update(record_id, fields, expected_version=5)


def test_missing_id_is_reported_before_version(store):
    store.add(ADA)
    with pytest.raises(KeyError):
        store.update(99, {"age": 1}, expected_version=5)
    with pytest.raises(KeyError):
        store.delete(99, expected_version=5)


def test_failed_validation_does_not_change_version(store):
    record_id = store.add(ADA)
    with pytest.raises(ValidationError):
        store.update(record_id, {"age": -1}, expected_version=1)
    assert store.get_version(record_id) == 1


def test_conflicting_delete_keeps_record(store):
    record_id = store.add(ADA)
    store.update(record_id, {"age": 37})
    with pytest.raises(ConflictError):
        store.delete(record_id, expected_version=1)
    assert store.list_ids() == [record_id]
    store.delete(record_id, expected_version=2)
    assert store.list_ids() == []


def test_versions_survive_reopening(store, path):
    record_id = store.add(ADA)
    store.update(record_id, {"age": 37})
    reopened = RecordStore(path)
    assert reopened.get_version(record_id) == 2
    with pytest.raises(ConflictError):
        reopened.update(record_id, {"age": 38}, expected_version=1)


def test_conflict_error_is_not_a_validation_error():
    assert not issubclass(ConflictError, ValidationError)
