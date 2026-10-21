"""Hidden tests for the initial pantry_inventory spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest private/test_pantry_initial.py
"""

import pytest
from pantry import Pantry, PantryError

BAD_QUANTITIES = [0, -1, 1.5, "2", None]
BAD_DAYS = [-1, 1.5, "3", None]


@pytest.fixture
def pantry():
    pan = Pantry()
    pan.add_item("milk", 2, 3)
    pan.add_item("rice", 10, 30)
    return pan


def state(pan):
    """Every item's batches, to check that a failed call changed nothing."""
    return {name: pan.get_batches(name) for name in pan.get_items()}


# --- adding -----------------------------------------------------------------


def test_a_new_pantry_has_no_items():
    pan = Pantry()
    assert pan.get_items() == []
    assert pan.get_expiring_by(100) == []


def test_items_are_listed_in_the_order_first_added():
    pan = Pantry()
    pan.add_item("rice", 1, 5)
    pan.add_item("milk", 1, 5)
    pan.add_item("rice", 1, 2)
    pan.add_item("beans", 1, 5)
    assert pan.get_items() == ["rice", "milk", "beans"]


def test_a_new_item_has_one_batch(pantry):
    assert pantry.get_quantity("milk") == 2
    assert pantry.get_batches("milk") == [(3, 2)]


def test_quantity_adds_up_over_batches(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.add_item("milk", 1, 1)
    assert pantry.get_quantity("milk") == 8
    assert pantry.get_quantity("rice") == 10


def test_batches_are_listed_earliest_use_by_first(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.add_item("milk", 1, 1)
    assert pantry.get_batches("milk") == [(1, 1), (3, 2), (8, 5)]


def test_batches_with_the_same_day_stay_separate_in_the_order_added(pantry):
    pantry.add_item("milk", 7, 3)
    pantry.add_item("milk", 4, 1)
    pantry.add_item("milk", 6, 3)
    assert pantry.get_batches("milk") == [(1, 4), (3, 2), (3, 7), (3, 6)]


@pytest.mark.parametrize("bad_name", [""])
def test_invalid_names_are_rejected(bad_name):
    pan = Pantry()
    with pytest.raises(ValueError):
        pan.add_item(bad_name, 1, 1)
    assert pan.get_items() == []


@pytest.mark.parametrize("quantity", BAD_QUANTITIES)
def test_invalid_quantities_are_rejected_when_adding(pantry, quantity):
    before = state(pantry)
    with pytest.raises(ValueError):
        pantry.add_item("milk", quantity, 3)
    with pytest.raises(ValueError):
        pantry.add_item("eggs", quantity, 3)
    assert state(pantry) == before
    assert pantry.get_items() == ["milk", "rice"]


@pytest.mark.parametrize("use_by", BAD_DAYS)
def test_invalid_use_by_days_are_rejected_when_adding(pantry, use_by):
    before = state(pantry)
    with pytest.raises(ValueError):
        pantry.add_item("milk", 1, use_by)
    with pytest.raises(ValueError):
        pantry.add_item("eggs", 1, use_by)
    assert state(pantry) == before
    assert pantry.get_items() == ["milk", "rice"]


def test_a_use_by_day_of_zero_is_allowed(pantry):
    pantry.add_item("eggs", 6, 0)
    assert pantry.get_batches("eggs") == [(0, 6)]
    assert pantry.get_expiring_by(0) == ["eggs"]


# --- using ------------------------------------------------------------------


def test_using_takes_from_the_earliest_batch(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.use_item("milk", 1)
    assert pantry.get_batches("milk") == [(3, 1), (8, 5)]
    assert pantry.get_quantity("milk") == 6


def test_using_spans_several_batches(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.add_item("milk", 1, 1)
    pantry.use_item("milk", 4)
    assert pantry.get_batches("milk") == [(8, 4)]


def test_using_breaks_ties_by_the_order_added(pantry):
    pantry.add_item("milk", 7, 3)
    pantry.use_item("milk", 3)
    assert pantry.get_batches("milk") == [(3, 6)]


def test_everything_can_be_used_and_the_item_stays_listed(pantry):
    pantry.use_item("milk", 2)
    assert pantry.get_quantity("milk") == 0
    assert pantry.get_batches("milk") == []
    assert pantry.get_items() == ["milk", "rice"]
    pantry.add_item("milk", 3, 9)
    assert pantry.get_batches("milk") == [(9, 3)]


def test_using_more_than_there_is_raises_and_changes_nothing(pantry):
    pantry.add_item("milk", 5, 8)
    before = state(pantry)
    with pytest.raises(PantryError):
        pantry.use_item("milk", 8)
    assert state(pantry) == before


def test_using_from_an_empty_item_raises(pantry):
    pantry.use_item("milk", 2)
    with pytest.raises(PantryError):
        pantry.use_item("milk", 1)


@pytest.mark.parametrize("quantity", BAD_QUANTITIES)
def test_invalid_quantities_are_rejected_when_using(pantry, quantity):
    before = state(pantry)
    with pytest.raises(ValueError):
        pantry.use_item("milk", quantity)
    assert state(pantry) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda pan: pan.use_item("eggs", 1),
        lambda pan: pan.get_quantity("eggs"),
        lambda pan: pan.get_batches("eggs"),
        lambda pan: pan.get_quantity(None),
        lambda pan: pan.get_quantity(1),
        lambda pan: pan.use_item(None, 1),
    ],
)
def test_names_that_are_not_items_raise_key_error(pantry, call):
    before = state(pantry)
    with pytest.raises(KeyError):
        call(pantry)
    assert state(pantry) == before


def test_an_unknown_item_is_reported_before_a_bad_quantity(pantry):
    with pytest.raises(KeyError):
        pantry.use_item("eggs", -1)


def test_a_bad_quantity_is_reported_before_a_shortage(pantry):
    # milk has 2, so 2.5 is also more than there is.
    with pytest.raises(ValueError):
        pantry.use_item("milk", 2.5)


# --- expiring ---------------------------------------------------------------


def test_expiring_by_includes_the_day_itself(pantry):
    assert pantry.get_expiring_by(2) == []
    assert pantry.get_expiring_by(3) == ["milk"]
    assert pantry.get_expiring_by(29) == ["milk"]
    assert pantry.get_expiring_by(30) == ["milk", "rice"]


def test_expiring_by_lists_items_in_the_order_first_added(pantry):
    pantry.add_item("beans", 1, 1)
    pantry.add_item("rice", 1, 2)
    assert pantry.get_expiring_by(5) == ["milk", "rice", "beans"]


def test_expiring_by_ignores_batches_that_are_used_up(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.use_item("milk", 2)
    assert pantry.get_expiring_by(3) == []
    assert pantry.get_expiring_by(8) == ["milk"]


def test_an_item_with_nothing_left_is_not_expiring(pantry):
    pantry.use_item("milk", 2)
    assert pantry.get_expiring_by(100) == ["rice"]


@pytest.mark.parametrize("day", BAD_DAYS)
def test_invalid_days_are_rejected(pantry, day):
    with pytest.raises(ValueError):
        pantry.get_expiring_by(day)


def test_pantries_do_not_share_items():
    first, second = Pantry(), Pantry()
    first.add_item("milk", 1, 1)
    assert second.get_items() == []
    second.add_item("milk", 5, 5)
    assert second.get_batches("milk") == [(5, 5)]
    assert first.get_batches("milk") == [(1, 1)]
