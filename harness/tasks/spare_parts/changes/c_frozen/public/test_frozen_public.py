"""Public checks for the c_frozen change (state flag). Shown to the editor,
never to the writer.

Usage (with parts.py importable, e.g. in the sandbox):
    python -m pytest changes/c_frozen/public/test_frozen_public.py
"""

import pytest
from parts import BinFrozen, PartsStore


@pytest.fixture
def store():
    s = PartsStore()
    s.add_bin("A1")
    s.add_bin("A2")
    s.stock("A1", "bolt", 5)
    return s


def test_bins_start_unfrozen(store):
    assert store.get_frozen("A1") is False
    store.set_frozen("A1", True)
    assert store.get_frozen("A1") is True


def test_a_frozen_bin_cannot_be_stocked(store):
    store.set_frozen("A1", True)
    with pytest.raises(BinFrozen):
        store.stock("A1", "bolt", 1)
    assert store.get_count("A1", "bolt") == 5


def test_a_frozen_bin_cannot_be_merged(store):
    store.set_frozen("A1", True)
    with pytest.raises(BinFrozen):
        store.merge_bins("A1", "A2")
    assert store.get_bins() == ["A1", "A2"]
    assert store.get_count("A1", "bolt") == 5
