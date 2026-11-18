"""Hidden tests for the c_frozen change (state flag). Never shown to the
writer or the editor.

Usage (with parts.py importable, e.g. in the sandbox):
    python -m pytest changes/c_frozen/private/test_frozen_new.py
"""

import pytest
from parts import BinFrozen, PartsStore, StoreError


@pytest.fixture
def store():
    s = PartsStore()
    for name in ["A1", "A2", "B1"]:
        s.add_bin(name)
    s.stock("A1", "bolt", 10)
    s.stock("A1", "nut", 4)
    s.stock("A2", "bolt", 2)
    return s


def state(s):
    return [
        (b, [(p, s.get_count(b, p)) for p in s.get_parts(b)], s.get_frozen(b))
        for b in s.get_bins()
    ]


# --- the flag ---------------------------------------------------------------


def test_bin_frozen_is_a_store_error():
    assert issubclass(BinFrozen, StoreError)


def test_every_bin_starts_unfrozen(store):
    store.add_bin("C1")
    assert [store.get_frozen(b) for b in store.get_bins()] == [False] * 4


def test_a_bin_can_be_frozen_and_unfrozen(store):
    store.set_frozen("A1", True)
    assert store.get_frozen("A1") is True
    assert store.get_frozen("A2") is False
    store.set_frozen("A1", False)
    assert store.get_frozen("A1") is False
    store.stock("A1", "bolt", 1)
    store.take("A1", "nut", 1)
    assert store.get_count("A1", "bolt") == 11
    assert store.get_count("A1", "nut") == 3


def test_bins_not_in_use_raise_key_error(store):
    store.scrap_bin("B1")
    for name in ["B1", "Z9"]:
        with pytest.raises(KeyError):
            store.set_frozen(name, True)
        with pytest.raises(KeyError):
            store.get_frozen(name)


def test_set_frozen_changes_no_counts_or_bins(store):
    before = [(b, [(p, store.get_count(b, p)) for p in store.get_parts(b)]) for b in store.get_bins()]
    store.set_frozen("A1", True)
    after = [(b, [(p, store.get_count(b, p)) for p in store.get_parts(b)]) for b in store.get_bins()]
    assert after == before


# --- calls on a frozen bin --------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.stock("A1", "bolt", 1),
        lambda s: s.stock("A1", "washer", 1),
        lambda s: s.take("A1", "bolt", 1),
        lambda s: s.take("A1", "nut", 4),
        lambda s: s.merge_bins("A1", "B1"),
        lambda s: s.merge_bins("A2", "A1"),
        lambda s: s.scrap_bin("A1"),
    ],
    ids=["stock", "stock_new_part", "take", "take_all", "merge_source", "merge_into", "scrap"],
)
def test_calls_on_a_frozen_bin_raise_and_change_nothing(store, call):
    store.set_frozen("A1", True)
    before = state(store)
    with pytest.raises(BinFrozen):
        call(store)
    assert state(store) == before


def test_merging_two_frozen_bins_raises(store):
    store.set_frozen("A1", True)
    store.set_frozen("A2", True)
    before = state(store)
    with pytest.raises(BinFrozen):
        store.merge_bins("A2", "A1")
    assert state(store) == before


def test_an_empty_frozen_bin_cannot_be_merged_or_scrapped(store):
    store.set_frozen("B1", True)
    before = state(store)
    with pytest.raises(BinFrozen):
        store.merge_bins("B1", "A1")
    with pytest.raises(BinFrozen):
        store.scrap_bin("B1")
    with pytest.raises(BinFrozen):
        store.merge_bins("A2", "B1")
    assert state(store) == before
    assert store.get_bins() == ["A1", "A2", "B1"]


# --- what still works -------------------------------------------------------


def test_other_bins_are_not_affected(store):
    store.set_frozen("A1", True)
    store.stock("A2", "bolt", 3)
    store.take("A2", "bolt", 1)
    assert store.merge_bins("A2", "B1") == 4
    assert store.scrap_bin("B1") == 4
    assert store.get_bins() == ["A1"]


def test_a_frozen_bin_can_still_be_read(store):
    store.set_frozen("A1", True)
    assert store.get_count("A1", "bolt") == 10
    assert store.get_parts("A1") == ["bolt", "nut"]
    assert store.get_bins() == ["A1", "A2", "B1"]


def test_bins_can_be_added_while_others_are_frozen(store):
    store.set_frozen("A1", True)
    store.add_bin("C1")
    store.stock("C1", "pin", 2)
    assert store.get_bins() == ["A1", "A2", "B1", "C1"]
    assert store.get_frozen("C1") is False


def test_an_unfrozen_bin_can_be_merged_and_scrapped_again(store):
    store.set_frozen("A1", True)
    store.set_frozen("A1", False)
    assert store.merge_bins("A2", "A1") == 2
    assert store.scrap_bin("A1") == 16
    assert store.get_bins() == ["B1"]
