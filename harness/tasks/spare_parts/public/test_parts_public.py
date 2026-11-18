"""Public checks for parts.py.

Usage (with parts.py importable, e.g. in the sandbox):
    python -m pytest public/test_parts_public.py
"""

import pytest
from parts import NotEnoughParts, PartsStore


@pytest.fixture
def store():
    s = PartsStore()
    s.add_bin("A1")
    s.add_bin("A2")
    return s


def test_stock_and_take_change_the_count(store):
    store.stock("A1", "bolt", 10)
    store.stock("A1", "bolt", 5)
    store.take("A1", "bolt", 12)
    assert store.get_count("A1", "bolt") == 3
    assert store.get_count("A1", "nut") == 0
    assert store.get_bins() == ["A1", "A2"]


def test_taking_more_than_there_are_raises(store):
    store.stock("A1", "bolt", 4)
    with pytest.raises(NotEnoughParts):
        store.take("A1", "bolt", 5)
    assert store.get_count("A1", "bolt") == 4


def test_a_part_whose_parts_were_all_taken_is_not_listed(store):
    store.stock("A1", "washer", 2)
    store.stock("A1", "bolt", 3)
    store.take("A1", "washer", 2)
    assert store.get_parts("A1") == ["bolt"]
    assert store.get_count("A1", "washer") == 0


def test_merge_bins_moves_every_part_and_removes_the_source(store):
    store.stock("A1", "bolt", 3)
    store.stock("A1", "nut", 4)
    store.stock("A2", "washer", 1)
    assert store.merge_bins("A1", "A2") == 7
    assert store.get_bins() == ["A2"]
    assert store.get_parts("A2") == ["bolt", "nut", "washer"]
    with pytest.raises(KeyError):
        store.get_parts("A1")


def test_scrap_bin_removes_the_bin_and_its_parts(store):
    store.stock("A2", "bolt", 6)
    assert store.scrap_bin("A2") == 6
    assert store.get_bins() == ["A1"]
    with pytest.raises(KeyError):
        store.get_count("A2", "bolt")
