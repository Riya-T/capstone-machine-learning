"""Hidden tests for the c_versions change (concurrency control). Never shown
to the writer or the editor.

Usage (with parts.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/private/test_versions_new.py
"""

import pytest
from parts import NotEnoughParts, PartsStore, StoreError, VersionConflict


@pytest.fixture
def store():
    s = PartsStore()
    for name in ["A1", "A2", "B1"]:
        s.add_bin(name)
    s.stock("A1", "bolt", 10)
    s.stock("A1", "nut", 4)
    s.stock("A2", "bolt", 2)
    return s  # version 6


def state(s):
    return [(b, [(p, s.get_count(b, p)) for p in s.get_parts(b)]) for b in s.get_bins()]


CHANGES = [
    lambda s, **kw: s.add_bin("C1", **kw),
    lambda s, **kw: s.stock("B1", "pin", 3, **kw),
    lambda s, **kw: s.take("A1", "nut", 1, **kw),
    lambda s, **kw: s.merge_bins("A2", "B1", **kw),
    lambda s, **kw: s.scrap_bin("A2", **kw),
]
IDS = ["add_bin", "stock", "take", "merge_bins", "scrap_bin"]


# --- the version number -----------------------------------------------------


def test_version_conflict_is_a_store_error():
    assert issubclass(VersionConflict, StoreError)


def test_a_new_store_is_at_version_0():
    assert PartsStore().get_version() == 0


def test_the_fixture_made_six_changes(store):
    assert store.get_version() == 6


@pytest.mark.parametrize("call", CHANGES, ids=IDS)
def test_each_change_raises_the_version_by_one(store, call):
    call(store)
    assert store.get_version() == 7


def test_merging_and_scrapping_raise_the_version_once(store):
    assert store.merge_bins("A1", "A2") == 14
    assert store.get_version() == 7
    assert store.scrap_bin("A2") == 16
    assert store.get_version() == 8
    assert store.get_bins() == ["B1"]


def test_reading_does_not_change_the_version(store):
    store.get_count("A1", "bolt")
    store.get_parts("A1")
    store.get_bins()
    store.get_version()
    assert store.get_version() == 6


def test_failed_calls_do_not_change_the_version(store):
    for call in (
        lambda: store.add_bin("A1"),
        lambda: store.stock("Z9", "bolt", 1),
        lambda: store.stock("A1", "bolt", 0),
        lambda: store.take("A1", "nut", 5),
        lambda: store.merge_bins("A1", "A1"),
        lambda: store.scrap_bin("Z9"),
    ):
        with pytest.raises((KeyError, ValueError, StoreError)):
            call()
    assert store.get_version() == 6


# --- expected_version -------------------------------------------------------


@pytest.mark.parametrize("call", CHANGES, ids=IDS)
def test_the_current_version_is_accepted(store, call):
    call(store, expected_version=6)
    assert store.get_version() == 7


@pytest.mark.parametrize("call", CHANGES, ids=IDS)
def test_none_is_accepted(store, call):
    call(store, expected_version=None)
    assert store.get_version() == 7


@pytest.mark.parametrize("expected", [5, 7, 0])
@pytest.mark.parametrize("call", CHANGES, ids=IDS)
def test_another_version_is_rejected_and_changes_nothing(store, call, expected):
    before = state(store)
    with pytest.raises(VersionConflict):
        call(store, expected_version=expected)
    assert state(store) == before
    assert store.get_version() == 6


def test_a_rejected_call_can_be_retried_with_the_new_version(store):
    seen = store.get_version()
    store.take("A1", "bolt", 1)  # someone else changes the store
    with pytest.raises(VersionConflict):
        store.take("A1", "bolt", 2, expected_version=seen)
    assert store.get_count("A1", "bolt") == 9
    store.take("A1", "bolt", 2, expected_version=store.get_version())
    assert store.get_count("A1", "bolt") == 7
    assert store.get_version() == 8


def test_versions_follow_a_sequence_of_changes():
    s = PartsStore()
    s.add_bin("A1", expected_version=0)
    s.add_bin("A2", expected_version=1)
    s.stock("A1", "bolt", 4, expected_version=2)
    s.merge_bins("A1", "A2", expected_version=3)
    with pytest.raises(VersionConflict):
        s.scrap_bin("A2", expected_version=3)
    assert s.scrap_bin("A2", expected_version=4) == 4
    assert s.get_version() == 5
    assert s.get_bins() == []


def test_other_errors_still_come_with_a_matching_version(store):
    with pytest.raises(NotEnoughParts):
        store.take("A1", "nut", 5, expected_version=6)
    with pytest.raises(KeyError):
        store.stock("Z9", "bolt", 1, expected_version=6)
    with pytest.raises(StoreError):
        store.add_bin("A1", expected_version=6)
    assert store.get_version() == 6
