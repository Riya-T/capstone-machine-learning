import pytest
from records import ConflictError, RecordStore

ADA = {"name": "Ada", "email": "ada@example.com", "age": 36}


def test_version_starts_at_one_and_increases(tmp_path):
    store = RecordStore(tmp_path / "db")
    record_id = store.add(ADA)
    assert store.get_version(record_id) == 1
    store.update(record_id, {"age": 37})
    assert store.get_version(record_id) == 2


def test_stale_update_raises_conflict(tmp_path):
    store = RecordStore(tmp_path / "db")
    record_id = store.add(ADA)
    store.update(record_id, {"age": 37})
    with pytest.raises(ConflictError):
        store.update(record_id, {"age": 38}, expected_version=1)
