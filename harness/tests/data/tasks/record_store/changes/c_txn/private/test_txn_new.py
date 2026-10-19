"""Hidden tests for the c_txn change (transactions). Never shown to the writer or
the editor.

Usage (with records.py importable, e.g. in the sandbox):
    python -m pytest changes/c_txn/private/test_txn_new.py
"""

import pytest
from records import RecordStore, ValidationError

ADA = {"name": "Ada", "email": "ada@example.com", "age": 36}
BOB = {"name": "Bob", "email": "bob@example.com", "age": 41}


class Boom(Exception):
    pass


@pytest.fixture
def path(tmp_path):
    return tmp_path / "db"


@pytest.fixture
def store(path):
    return RecordStore(path)


def snapshot(store):
    return {record_id: store.get(record_id) for record_id in store.list_ids()}


def test_reads_inside_the_block_see_its_changes(store):
    with store.transaction():
        record_id = store.add(ADA)
        store.update(record_id, {"age": 50})
        assert store.get(record_id)["age"] == 50


def test_file_is_written_only_when_the_block_exits(store, path):
    store.add(ADA)
    with store.transaction():
        store.add(BOB)
        assert RecordStore(path).list_ids() == [1]
    assert RecordStore(path).list_ids() == [1, 2]


def test_rollback_restores_adds_updates_and_deletes(store, path):
    first = store.add(ADA)
    second = store.add(BOB)
    before = snapshot(store)
    with pytest.raises(Boom), store.transaction():
        store.add({**ADA, "email": "ada2@example.com"})
        store.update(first, {"name": "Changed"})
        store.delete(second)
        raise Boom
    assert snapshot(store) == before
    assert snapshot(RecordStore(path)) == before


def test_the_original_exception_propagates(store):
    error = Boom("original")
    with pytest.raises(Boom) as caught, store.transaction():
        raise error
    assert caught.value is error


def test_escaping_validation_error_undoes_earlier_changes(store):
    with pytest.raises(ValidationError), store.transaction():
        store.add(ADA)
        store.add({**BOB, "age": -1})
    assert store.list_ids() == []


def test_caught_failure_inside_block_keeps_other_changes(store, path):
    with store.transaction():
        store.add(ADA)
        with pytest.raises(ValidationError):
            store.add({**BOB, "age": -1})
        store.add(BOB)
    assert [r["name"] for r in snapshot(RecordStore(path)).values()] == ["Ada", "Bob"]


def test_nested_transaction_raises_runtime_error(store):
    with pytest.raises(RuntimeError), store.transaction():
        store.add(ADA)
        with store.transaction():
            pass
    assert store.list_ids() == []


def test_store_is_usable_after_rollback(store, path):
    with pytest.raises(Boom), store.transaction():
        store.add(ADA)
        raise Boom
    with store.transaction():
        record_id = store.add(BOB)
    assert RecordStore(path).get(record_id) == BOB
    assert store.add(ADA) > record_id
