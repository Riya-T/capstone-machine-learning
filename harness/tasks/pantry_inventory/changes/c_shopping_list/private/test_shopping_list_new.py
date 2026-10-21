"""Hidden tests for the c_shopping_list change (minimum stock and a
shopping list). Never shown to the writer or the editor.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_shopping_list/private/test_shopping_list_new.py
"""

import pytest
from pantry import Pantry

BAD_VALUES = [-1, 1.5, "3", None, True]
BAD_DAYS = [-1, 1.5, "3", True]  # None is the default: no day


@pytest.fixture
def pantry():
    pan = Pantry()
    pan.add_item("milk", 2, 3)
    pan.add_item("milk", 4, 8)
    pan.add_item("rice", 10, 30)
    pan.add_item("eggs", 6, 5)
    return pan


def state(pan):
    return {name: (pan.get_batches(name), pan.get_minimum(name)) for name in pan.get_items()}


def test_every_item_starts_with_a_minimum_of_zero(pantry):
    assert [pantry.get_minimum(n) for n in pantry.get_items()] == [0, 0, 0]
    assert pantry.get_shopping_list() == []


def test_the_list_follows_the_order_items_were_first_added(pantry):
    pantry.set_minimum("eggs", 12)
    pantry.set_minimum("milk", 10)
    assert pantry.get_shopping_list() == [("milk", 4), ("eggs", 6)]


def test_an_item_exactly_at_its_minimum_is_left_out(pantry):
    pantry.set_minimum("rice", 10)
    assert pantry.get_shopping_list() == []
    pantry.use_item("rice", 1)
    assert pantry.get_shopping_list() == [("rice", 1)]


def test_an_item_with_nothing_left_needs_its_whole_minimum(pantry):
    pantry.set_minimum("eggs", 4)
    pantry.use_item("eggs", 6)
    assert pantry.get_shopping_list() == [("eggs", 4)]


def test_adding_and_using_keep_the_minimum(pantry):
    pantry.set_minimum("milk", 8)
    pantry.add_item("milk", 1, 9)
    pantry.use_item("milk", 3)
    assert pantry.get_minimum("milk") == 8
    assert pantry.get_shopping_list() == [("milk", 4)]


def test_setting_the_minimum_again_replaces_it(pantry):
    pantry.set_minimum("rice", 20)
    pantry.set_minimum("rice", 0)
    assert pantry.get_minimum("rice") == 0
    assert pantry.get_shopping_list() == []


def test_a_day_counts_only_batches_still_good_on_that_day(pantry):
    pantry.set_minimum("milk", 5)
    pantry.set_minimum("eggs", 6)
    assert pantry.get_shopping_list(day=3) == []
    assert pantry.get_shopping_list(day=4) == [("milk", 1)]
    assert pantry.get_shopping_list(day=5) == [("milk", 1)]
    assert pantry.get_shopping_list(day=6) == [("milk", 1), ("eggs", 6)]
    assert pantry.get_shopping_list(day=9) == [("milk", 5), ("eggs", 6)]


def test_a_day_of_zero_counts_every_batch(pantry):
    pantry.set_minimum("milk", 7)
    assert pantry.get_shopping_list(day=0) == [("milk", 1)]
    assert pantry.get_shopping_list() == [("milk", 1)]


def test_a_day_follows_the_batches_left_after_using(pantry):
    pantry.set_minimum("milk", 4)
    pantry.use_item("milk", 3)  # takes the day-3 batch and one from day 8
    assert pantry.get_shopping_list() == [("milk", 1)]
    assert pantry.get_shopping_list(day=4) == [("milk", 1)]


@pytest.mark.parametrize("minimum", BAD_VALUES)
def test_invalid_minimums_are_rejected(pantry, minimum):
    pantry.set_minimum("milk", 3)
    before = state(pantry)
    with pytest.raises(ValueError):
        pantry.set_minimum("milk", minimum)
    assert state(pantry) == before


@pytest.mark.parametrize("day", BAD_DAYS)
def test_invalid_days_are_rejected(pantry, day):
    with pytest.raises(ValueError):
        pantry.get_shopping_list(day=day)


@pytest.mark.parametrize(
    "call",
    [
        lambda pan: pan.set_minimum("bread", 1),
        lambda pan: pan.get_minimum("bread"),
        lambda pan: pan.get_minimum(None),
        lambda pan: pan.set_minimum(1, 1),
    ],
)
def test_names_that_are_not_items_raise_key_error(pantry, call):
    before = state(pantry)
    with pytest.raises(KeyError):
        call(pantry)
    assert state(pantry) == before


def test_an_unknown_item_is_reported_before_a_bad_minimum(pantry):
    with pytest.raises(KeyError):
        pantry.set_minimum("bread", -1)
