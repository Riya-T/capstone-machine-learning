"""Hidden tests for the initial spare_parts spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with parts.py importable, e.g. in the sandbox):
    python -m pytest private/test_parts_initial.py
"""

import pytest
from parts import NotEnoughParts, PartsStore, StoreError


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
    """Every bin in order with its part numbers and counts, to check that a
    failed call changed nothing."""
    return [(b, [(p, s.get_count(b, p)) for p in s.get_parts(b)]) for b in s.get_bins()]


# --- bins -------------------------------------------------------------------


def test_a_new_bin_is_empty():
    s = PartsStore()
    s.add_bin("A1")
    assert s.get_parts("A1") == []
    assert s.get_count("A1", "bolt") == 0


def test_bins_are_listed_in_the_order_added():
    s = PartsStore()
    for name in ["C3", "A1", "B2"]:
        s.add_bin(name)
    assert s.get_bins() == ["C3", "A1", "B2"]


def test_adding_a_name_in_use_is_rejected(store):
    before = state(store)
    with pytest.raises(StoreError):
        store.add_bin("A1")
    assert state(store) == before


BIN_CALLS = [
    lambda s, b: s.stock(b, "bolt", 1),
    lambda s, b: s.take(b, "bolt", 1),
    lambda s, b: s.merge_bins(b, "A2"),
    lambda s, b: s.merge_bins("A1", b),
    lambda s, b: s.scrap_bin(b),
    lambda s, b: s.get_count(b, "bolt"),
    lambda s, b: s.get_parts(b),
]


@pytest.mark.parametrize("call", BIN_CALLS)
def test_bins_that_were_never_added_raise_key_error(store, call):
    before = state(store)
    with pytest.raises(KeyError):
        call(store, "Z9")
    assert state(store) == before


@pytest.mark.parametrize("call", BIN_CALLS)
def test_a_merged_bin_is_not_in_use(store, call):
    store.stock("B1", "bolt", 1)
    store.merge_bins("B1", "A2")
    before = state(store)
    with pytest.raises(KeyError):
        call(store, "B1")
    assert state(store) == before


@pytest.mark.parametrize("call", BIN_CALLS)
def test_a_scrapped_bin_is_not_in_use(store, call):
    store.stock("B1", "bolt", 1)
    store.scrap_bin("B1")
    before = state(store)
    with pytest.raises(KeyError):
        call(store, "B1")
    assert state(store) == before


# --- stocking and taking ----------------------------------------------------


def test_stock_and_take_change_only_that_count(store):
    store.stock("A1", "bolt", 5)
    store.take("A1", "nut", 1)
    store.stock("B1", "nut", 7)
    assert store.get_count("A1", "bolt") == 15
    assert store.get_count("A1", "nut") == 3
    assert store.get_count("B1", "nut") == 7
    assert store.get_count("A2", "bolt") == 2
    assert store.get_count("A2", "nut") == 0


def test_every_part_of_a_number_can_be_taken(store):
    store.take("A1", "bolt", 10)
    assert store.get_count("A1", "bolt") == 0
    assert store.get_parts("A1") == ["nut"]
    store.stock("A1", "bolt", 1)
    assert store.get_parts("A1") == ["bolt", "nut"]


def test_parts_are_listed_in_alphabetical_order(store):
    for part in ["washer", "anchor", "pin"]:
        store.stock("B1", part, 1)
    assert store.get_parts("B1") == ["anchor", "pin", "washer"]


def test_taking_more_than_there_are_changes_nothing(store):
    before = state(store)
    with pytest.raises(NotEnoughParts):
        store.take("A1", "nut", 5)
    with pytest.raises(NotEnoughParts):
        store.take("A1", "washer", 1)
    with pytest.raises(NotEnoughParts):
        store.take("B1", "bolt", 1)
    assert state(store) == before


@pytest.mark.parametrize("count", [0, -3])
@pytest.mark.parametrize("call", [lambda s, c: s.stock("A1", "bolt", c)], ids=["stock"])
def test_counts_of_0_or_less_are_rejected(store, call, count):
    before = state(store)
    with pytest.raises(ValueError):
        call(store, count)
    assert state(store) == before


# --- merging ----------------------------------------------------------------


def test_merge_bins_adds_to_the_counts_already_there(store):
    store.stock("A2", "washer", 3)
    assert store.merge_bins("A1", "A2") == 14
    assert store.get_count("A2", "bolt") == 12
    assert store.get_count("A2", "nut") == 4
    assert store.get_count("A2", "washer") == 3
    assert store.get_parts("A2") == ["bolt", "nut", "washer"]
    assert store.get_bins() == ["A2", "B1"]


def test_merging_an_empty_bin_moves_nothing(store):
    assert store.merge_bins("B1", "A1") == 0
    assert store.get_bins() == ["A1", "A2"]
    assert store.get_count("A1", "bolt") == 10


def test_merging_into_an_empty_bin(store):
    assert store.merge_bins("A2", "B1") == 2
    assert store.get_parts("B1") == ["bolt"]
    assert store.get_count("B1", "bolt") == 2
    assert store.get_bins() == ["A1", "B1"]


def test_merging_a_bin_into_itself_is_rejected(store):
    before = state(store)
    with pytest.raises(ValueError):
        store.merge_bins("A1", "A1")
    with pytest.raises(ValueError):
        store.merge_bins("B1", "B1")
    assert state(store) == before


# --- scrapping --------------------------------------------------------------


def test_scrap_bin_returns_how_many_parts_were_thrown_away(store):
    assert store.scrap_bin("A1") == 14
    assert store.get_bins() == ["A2", "B1"]
    assert store.get_count("A2", "bolt") == 2


def test_scrapping_an_empty_bin(store):
    assert store.scrap_bin("B1") == 0
    assert store.get_bins() == ["A1", "A2"]


def test_the_other_bins_keep_their_order(store):
    store.add_bin("C1")
    store.scrap_bin("A2")
    store.merge_bins("A1", "C1")
    assert store.get_bins() == ["B1", "C1"]
    assert store.get_count("C1", "bolt") == 10


# --- general ----------------------------------------------------------------


def test_not_enough_parts_is_a_store_error():
    assert issubclass(NotEnoughParts, StoreError)


def test_stores_do_not_share_bins():
    first, second = PartsStore(), PartsStore()
    first.add_bin("A1")
    first.stock("A1", "bolt", 3)
    assert second.get_bins() == []
    second.add_bin("A1")
    assert second.get_count("A1", "bolt") == 0
