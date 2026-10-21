"""Hidden tests for the c_expired change (the current day and expired
batches). Never shown to the writer or the editor.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_expired/private/test_expired_new.py
"""

import pytest
from pantry import Pantry, PantryError


@pytest.fixture
def pantry():
    pan = Pantry()
    pan.add_item("milk", 2, 3)
    pan.add_item("milk", 5, 8)
    pan.add_item("rice", 10, 30)
    return pan


def state(pan):
    return {name: pan.get_batches(name) for name in pan.get_items()}


def test_nothing_is_expired_on_day_zero(pantry):
    assert pantry.get_day() == 0
    assert pantry.get_usable_quantity("milk") == 7
    assert pantry.get_expired_quantity("milk") == 0
    assert pantry.get_expired_quantity("rice") == 0


def test_a_batch_is_usable_on_its_use_by_day_and_expired_after(pantry):
    pantry.set_day(3)
    assert pantry.get_usable_quantity("milk") == 7
    assert pantry.get_expired_quantity("milk") == 0
    pantry.set_day(4)
    assert pantry.get_usable_quantity("milk") == 5
    assert pantry.get_expired_quantity("milk") == 2


def test_usable_and_expired_add_up_to_the_quantity(pantry):
    pantry.set_day(9)
    assert pantry.get_usable_quantity("milk") == 0
    assert pantry.get_expired_quantity("milk") == 7
    assert pantry.get_quantity("milk") == 7
    assert pantry.get_batches("milk") == [(3, 2), (8, 5)]


def test_using_skips_expired_batches(pantry):
    pantry.set_day(4)
    pantry.use_item("milk", 1)
    assert pantry.get_batches("milk") == [(3, 2), (8, 4)]
    assert pantry.get_usable_quantity("milk") == 4


def test_using_more_than_the_usable_amount_changes_nothing(pantry):
    pantry.set_day(4)
    before = state(pantry)
    with pytest.raises(PantryError):
        pantry.use_item("milk", 6)
    assert state(pantry) == before
    pantry.set_day(9)
    with pytest.raises(PantryError):
        pantry.use_item("milk", 1)
    assert state(pantry) == before


def test_using_takes_from_the_earliest_usable_batch(pantry):
    pantry.add_item("milk", 3, 6)
    pantry.set_day(4)
    pantry.use_item("milk", 4)
    assert pantry.get_batches("milk") == [(3, 2), (8, 4)]


def test_discarding_returns_the_units_thrown_away(pantry):
    pantry.add_item("milk", 3, 1)
    pantry.set_day(4)
    assert pantry.discard_expired("milk") == 5
    assert pantry.get_batches("milk") == [(8, 5)]
    assert pantry.get_quantity("milk") == 5
    assert pantry.get_expired_quantity("milk") == 0
    assert pantry.discard_expired("milk") == 0


def test_discarding_leaves_other_items_alone(pantry):
    pantry.set_day(4)
    before = pantry.get_batches("rice")
    pantry.discard_expired("milk")
    assert pantry.get_batches("rice") == before
    assert pantry.discard_expired("rice") == 0


def test_discarding_everything_leaves_the_item_listed(pantry):
    pantry.set_day(20)
    assert pantry.discard_expired("milk") == 7
    assert pantry.get_items() == ["milk", "rice"]
    assert pantry.get_batches("milk") == []


def test_the_day_can_stay_but_never_go_back(pantry):
    pantry.set_day(5)
    pantry.set_day(5)
    with pytest.raises(ValueError):
        pantry.set_day(4)
    assert pantry.get_day() == 5
    pantry.set_day(6)
    assert pantry.get_day() == 6


@pytest.mark.parametrize("day", [-1, 1.5, "3", None, True])
def test_invalid_days_are_rejected_when_setting(pantry, day):
    pantry.set_day(2)
    with pytest.raises(ValueError):
        pantry.set_day(day)
    assert pantry.get_day() == 2


def test_setting_the_day_changes_no_batches(pantry):
    before = state(pantry)
    pantry.set_day(10)
    assert state(pantry) == before


@pytest.mark.parametrize("method", ["get_usable_quantity", "get_expired_quantity", "discard_expired"])
@pytest.mark.parametrize("name", ["eggs", None, 1])
def test_new_methods_raise_key_error_for_names_that_are_not_items(pantry, method, name):
    with pytest.raises(KeyError):
        getattr(pantry, method)(name)


def test_batches_added_on_the_current_day_are_usable(pantry):
    pantry.set_day(10)
    pantry.add_item("milk", 4, 10)
    assert pantry.get_usable_quantity("milk") == 4
    pantry.use_item("milk", 4)
    assert pantry.get_batches("milk") == [(3, 2), (8, 5)]
