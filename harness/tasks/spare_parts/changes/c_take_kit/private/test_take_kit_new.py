"""Hidden tests for the c_take_kit change (atomic operation). Never shown to
the writer or the editor.

Usage (with parts.py importable, e.g. in the sandbox):
    python -m pytest changes/c_take_kit/private/test_take_kit_new.py
"""

import pytest
from parts import NotEnoughParts, PartsStore


@pytest.fixture
def store():
    s = PartsStore()
    for name in ["A1", "A2", "B1"]:
        s.add_bin(name)
    s.stock("A1", "bolt", 10)
    s.stock("A1", "nut", 6)
    s.stock("A1", "washer", 3)
    s.stock("A2", "bolt", 2)
    return s


def state(s):
    return [(b, [(p, s.get_count(b, p)) for p in s.get_parts(b)]) for b in s.get_bins()]


# --- kits that can be handed out --------------------------------------------


def test_a_kit_of_one_part_number_is_like_take(store):
    assert store.take_kit("A1", {"nut": 2}) == 2
    assert store.get_count("A1", "nut") == 4
    assert store.get_count("A1", "bolt") == 10


def test_a_kit_of_several_part_numbers(store):
    assert store.take_kit("A1", {"bolt": 4, "nut": 4, "washer": 1}) == 9
    assert state(store)[0] == ("A1", [("bolt", 6), ("nut", 2), ("washer", 2)])


def test_a_kit_may_take_the_last_parts_of_a_number(store):
    assert store.take_kit("A1", {"washer": 3, "bolt": 1}) == 4
    assert store.get_parts("A1") == ["bolt", "nut"]
    assert store.get_count("A1", "washer") == 0


def test_a_kit_changes_only_its_own_bin(store):
    store.take_kit("A2", {"bolt": 2})
    assert store.get_parts("A2") == []
    assert store.get_count("A1", "bolt") == 10
    assert store.get_bins() == ["A1", "A2", "B1"]


def test_kits_can_be_taken_one_after_another(store):
    store.take_kit("A1", {"bolt": 4, "nut": 3})
    store.take_kit("A1", {"bolt": 4, "nut": 3})
    assert store.get_count("A1", "bolt") == 2
    assert store.get_parts("A1") == ["bolt", "washer"]
    with pytest.raises(NotEnoughParts):
        store.take_kit("A1", {"bolt": 1, "nut": 1})


# --- kits that cannot be handed out -----------------------------------------


def test_too_few_of_the_last_part_number_takes_nothing(store):
    before = state(store)
    with pytest.raises(NotEnoughParts):
        store.take_kit("A1", {"bolt": 2, "nut": 2, "washer": 4})
    assert state(store) == before


def test_too_few_of_the_first_part_number_takes_nothing(store):
    before = state(store)
    with pytest.raises(NotEnoughParts):
        store.take_kit("A1", {"bolt": 11, "nut": 2})
    assert state(store) == before


def test_a_part_number_the_bin_does_not_have_takes_nothing(store):
    before = state(store)
    with pytest.raises(NotEnoughParts):
        store.take_kit("A1", {"bolt": 1, "pin": 1})
    with pytest.raises(NotEnoughParts):
        store.take_kit("B1", {"bolt": 1})
    assert state(store) == before


@pytest.mark.parametrize("count", [0, -2])
def test_a_count_of_0_or_less_takes_nothing(store, count):
    before = state(store)
    with pytest.raises(ValueError):
        store.take_kit("A1", {"bolt": 1, "nut": count})
    assert state(store) == before


def test_a_bin_not_in_use_raises_key_error(store):
    store.scrap_bin("B1")
    before = state(store)
    for name in ["B1", "Z9"]:
        with pytest.raises(KeyError):
            store.take_kit(name, {"bolt": 1})
    assert state(store) == before


def test_the_store_works_normally_after_a_failed_kit(store):
    with pytest.raises(NotEnoughParts):
        store.take_kit("A1", {"bolt": 5, "washer": 5})
    store.take("A1", "bolt", 10)
    assert store.get_parts("A1") == ["nut", "washer"]
    assert store.take_kit("A1", {"washer": 3}) == 3
