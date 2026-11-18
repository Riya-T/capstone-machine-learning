"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with parts.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from parts import PartsStore, StoreError


@pytest.fixture
def store():
    s = PartsStore()
    s.add_bin("A1")
    s.add_bin("A2")
    return s


def test_undo_takes_back_the_last_stock(store):
    store.stock("A1", "bolt", 5)
    store.stock("A1", "bolt", 2)
    store.undo()
    assert store.get_count("A1", "bolt") == 5
    store.undo()
    assert store.get_parts("A1") == []


def test_undo_takes_back_a_take(store):
    store.stock("A1", "bolt", 5)
    store.take("A1", "bolt", 3)
    store.undo()
    assert store.get_count("A1", "bolt") == 5


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(StoreError):
        PartsStore().undo()
