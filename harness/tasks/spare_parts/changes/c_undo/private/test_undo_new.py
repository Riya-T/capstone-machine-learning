"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with parts.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
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
    return [(b, [(p, s.get_count(b, p)) for p in s.get_parts(b)]) for b in s.get_bins()]


# --- each call can be undone ------------------------------------------------


def test_undo_of_stocking_a_new_part_number(store):
    before = state(store)
    store.stock("B1", "washer", 6)
    store.undo()
    assert state(store) == before
    assert store.get_parts("B1") == []


def test_undo_of_stocking_more_of_a_part_number(store):
    store.stock("A1", "bolt", 5)
    store.undo()
    assert store.get_count("A1", "bolt") == 10


def test_undo_of_a_take(store):
    before = state(store)
    store.take("A1", "bolt", 3)
    store.undo()
    assert state(store) == before


def test_undo_of_taking_the_last_parts_lists_the_part_again(store):
    before = state(store)
    store.take("A1", "nut", 4)
    assert store.get_parts("A1") == ["bolt"]
    store.undo()
    assert state(store) == before
    assert store.get_parts("A1") == ["bolt", "nut"]


def test_undo_of_merge_bins_brings_the_source_back(store):
    before = state(store)
    assert store.merge_bins("A1", "A2") == 14
    store.undo()
    assert state(store) == before
    assert store.get_bins() == ["A1", "A2", "B1"]
    assert store.get_count("A2", "bolt") == 2
    assert store.get_parts("A2") == ["bolt"]


def test_undo_of_merge_bins_keeps_the_source_in_its_place(store):
    store.add_bin("C1")
    store.stock("C1", "pin", 1)
    before = state(store)
    store.merge_bins("A2", "C1")
    assert store.get_bins() == ["A1", "B1", "C1"]
    store.undo()
    assert store.get_bins() == ["A1", "A2", "B1", "C1"]
    assert state(store) == before


def test_undo_of_merging_into_an_empty_bin(store):
    before = state(store)
    store.merge_bins("A1", "B1")
    store.undo()
    assert state(store) == before
    assert store.get_parts("B1") == []


def test_undo_of_scrap_bin_brings_it_back_with_its_parts(store):
    before = state(store)
    assert store.scrap_bin("A1") == 14
    store.undo()
    assert state(store) == before
    assert store.get_bins() == ["A1", "A2", "B1"]


def test_undo_of_scrap_bin_keeps_its_place_in_the_list(store):
    store.add_bin("C1")
    before = state(store)
    store.scrap_bin("A2")
    store.undo()
    assert store.get_bins() == ["A1", "A2", "B1", "C1"]
    assert state(store) == before


def test_a_bin_brought_back_is_in_use_again(store):
    store.merge_bins("A2", "A1")
    store.undo()
    store.stock("A2", "bolt", 1)
    assert store.get_count("A2", "bolt") == 3
    with pytest.raises(StoreError):
        store.add_bin("A2")
    store.scrap_bin("A1")
    store.undo()
    assert store.merge_bins("A2", "A1") == 3
    assert store.get_count("A1", "bolt") == 13
    assert store.get_bins() == ["A1", "B1"]


def test_merging_or_scrapping_an_empty_bin_can_be_undone(store):
    assert store.merge_bins("B1", "A1") == 0
    store.undo()
    assert store.get_bins() == ["A1", "A2", "B1"]
    assert store.scrap_bin("B1") == 0
    store.undo()
    assert store.get_bins() == ["A1", "A2", "B1"]
    store.undo()  # the stock of A2's bolts
    assert store.get_parts("A2") == []


def test_undo_of_add_bin_removes_it_and_frees_the_name(store):
    store.add_bin("C1")
    store.undo()
    assert store.get_bins() == ["A1", "A2", "B1"]
    with pytest.raises(KeyError):
        store.get_parts("C1")
    store.add_bin("C1")
    assert store.get_bins() == ["A1", "A2", "B1", "C1"]
    assert store.get_parts("C1") == []


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    s = PartsStore()
    calls = [
        lambda: s.add_bin("A1"),
        lambda: s.add_bin("A2"),
        lambda: s.stock("A1", "bolt", 5),
        lambda: s.stock("A1", "nut", 2),
        lambda: s.add_bin("B1"),
        lambda: s.stock("A2", "bolt", 4),
        lambda: s.take("A1", "bolt", 1),
        lambda: s.merge_bins("A2", "B1"),
        lambda: s.stock("B1", "pin", 3),
        lambda: s.take("A1", "nut", 2),
        lambda: s.add_bin("C1"),
        lambda: s.merge_bins("A1", "B1"),
        lambda: s.stock("C1", "nut", 1),
        lambda: s.scrap_bin("C1"),
    ]
    states = [state(s)]
    for call in calls:
        call()
        states.append(state(s))
    assert s.get_bins() == ["B1"]
    assert s.get_count("B1", "bolt") == 8
    assert s.get_count("B1", "pin") == 3
    for expected in reversed(states[:-1]):
        s.undo()
        assert state(s) == expected
    with pytest.raises(StoreError):
        s.undo()
    assert s.get_bins() == []


def test_failed_calls_are_not_recorded(store):
    store.stock("B1", "pin", 2)
    for call in (
        lambda: store.take("A1", "bolt", 99),
        lambda: store.take("B1", "bolt", 1),
        lambda: store.stock("A1", "bolt", 0),
        lambda: store.stock("Z9", "bolt", 1),
        lambda: store.merge_bins("A1", "A1"),
        lambda: store.merge_bins("A1", "Z9"),
        lambda: store.scrap_bin("Z9"),
        lambda: store.add_bin("A1"),
    ):
        with pytest.raises((ValueError, KeyError, StoreError)):
            call()
    store.undo()  # the stock of the pins
    assert store.get_parts("B1") == []
    assert store.get_count("A1", "bolt") == 10


def test_get_calls_are_not_recorded(store):
    store.stock("B1", "pin", 2)
    store.get_count("B1", "pin")
    store.get_parts("B1")
    store.get_bins()
    store.undo()
    assert store.get_parts("B1") == []
    assert store.get_count("A2", "bolt") == 2


def test_there_is_no_redo():
    s = PartsStore()
    s.add_bin("A1")
    s.stock("A1", "bolt", 3)
    s.undo()
    s.undo()
    assert s.get_bins() == []
    with pytest.raises(StoreError):
        s.undo()


def test_new_calls_after_an_undo_are_undone_first(store):
    store.take("A1", "bolt", 1)
    store.undo()
    store.stock("B1", "pin", 1)
    store.undo()
    assert store.get_parts("B1") == []
    assert store.get_count("A1", "bolt") == 10
    store.undo()  # the stock of A2's bolts in the fixture
    assert store.get_parts("A2") == []
    assert store.get_parts("A1") == ["bolt", "nut"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    s = PartsStore()
    with pytest.raises(StoreError):
        s.undo()
    s.add_bin("A1")
    s.undo()
    with pytest.raises(StoreError):
        s.undo()
    assert s.get_bins() == []
    s.add_bin("A1")
    s.stock("A1", "bolt", 1)
    assert s.get_count("A1", "bolt") == 1


def test_the_whole_fixture_can_be_undone(store):
    for _ in range(6):
        store.undo()
    assert store.get_bins() == []
    with pytest.raises(StoreError):
        store.undo()


def test_undo_restores_counts_that_a_later_call_checks(store):
    store.take("A1", "nut", 4)
    store.undo()
    store.take("A1", "nut", 3)
    assert store.get_count("A1", "nut") == 1
    store.scrap_bin("A2")
    store.undo()
    with pytest.raises(NotEnoughParts):
        store.take("A2", "bolt", 3)
    store.take("A2", "bolt", 2)
    assert store.get_parts("A2") == []
