"""Public checks for the c_txn change (transactions). Shown to the editor,
never to the writer.

Usage (with records.py importable, e.g. in the task sandbox):
    python -m pytest changes/c_txn/public/test_txn_public.py
"""

import pytest
from records import RecordStore

ADA = {"name": "Ada", "email": "ada@example.com", "age": 36}


def test_transaction_saves_all_changes(tmp_path):
    store = RecordStore(tmp_path / "db")
    with store.transaction():
        first = store.add(ADA)
        store.update(first, {"age": 37})
    assert RecordStore(tmp_path / "db").get(first) == {**ADA, "age": 37}


def test_exception_undoes_the_transaction(tmp_path):
    store = RecordStore(tmp_path / "db")
    with pytest.raises(ValueError), store.transaction():
        store.add(ADA)
        raise ValueError("abort")
    assert store.list_ids() == []
