"""Hidden tests for the c_unique change (unique emails). Never shown to the writer or
the editor.

Usage (with records.py importable, e.g. in the sandbox):
    python -m pytest changes/c_unique/private/test_unique_new.py
"""

import pytest
from records import RecordStore, ValidationError

ADA = {"name": "Ada", "email": "ada@example.com", "age": 36}
BOB = {"name": "Bob", "email": "bob@example.com", "age": 41}


@pytest.fixture
def path(tmp_path):
    return tmp_path / "db"


@pytest.fixture
def store(path):
    return RecordStore(path)


def test_duplicate_add_changes_nothing(store, path):
    store.add(ADA)
    with pytest.raises(ValidationError):
        store.add({**BOB, "email": ADA["email"]})
    assert store.list_ids() == [1]
    assert store.add(BOB) == 2


@pytest.mark.parametrize("email", ["ADA@EXAMPLE.COM", "Ada@Example.com"])
def test_comparison_ignores_case(store, email):
    store.add(ADA)
    with pytest.raises(ValidationError):
        store.add({**BOB, "email": email})


def test_update_to_another_records_email_is_rejected(store):
    store.add(ADA)
    bob = store.add(BOB)
    with pytest.raises(ValidationError):
        store.update(bob, {"email": "Ada@example.com"})
    assert store.get(bob) == BOB


def test_update_to_own_email_is_allowed(store):
    record_id = store.add(ADA)
    store.update(record_id, {"email": "ADA@example.com", "age": 37})
    assert store.get(record_id) == {**ADA, "email": "ADA@example.com", "age": 37}


def test_delete_frees_the_email(store):
    record_id = store.add(ADA)
    store.delete(record_id)
    assert store.add({**BOB, "email": ADA["email"]}) == 2


def test_uniqueness_applies_to_saved_records(store, path):
    store.add(ADA)
    with pytest.raises(ValidationError):
        RecordStore(path).add({**BOB, "email": ADA["email"]})
