"""Hidden tests for the c_categories change (item categories). Never shown
to the writer or the editor.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_categories/private/test_categories_new.py
"""

import pytest
from pantry import Pantry

BAD_CATEGORIES = ["", 3, 1.5, ["dairy"]]


@pytest.fixture
def pantry():
    pan = Pantry()
    pan.add_item("milk", 2, 3, category="dairy")
    pan.add_item("rice", 10, 30)
    pan.add_item("cheese", 1, 9, category="dairy")
    return pan


def state(pan):
    return {name: (pan.get_batches(name), pan.get_category(name)) for name in pan.get_items()}


def test_items_without_a_category_go_to_other(pantry):
    assert pantry.get_category("rice") == "other"
    assert pantry.get_items_in("other") == ["rice"]
    assert pantry.get_category_quantity("other") == 10


def test_adding_without_a_category_keeps_the_current_one(pantry):
    pantry.add_item("milk", 4, 8)
    assert pantry.get_category("milk") == "dairy"
    assert pantry.get_category_quantity("dairy") == 7


def test_adding_with_a_category_moves_the_item(pantry):
    pantry.add_item("cheese", 2, 12, category="deli")
    assert pantry.get_category("cheese") == "deli"
    assert pantry.get_items_in("dairy") == ["milk"]
    assert pantry.get_items_in("deli") == ["cheese"]
    assert pantry.get_quantity("cheese") == 3


def test_set_category_moves_the_item_and_updates_the_lists(pantry):
    pantry.set_category("rice", "grains")
    pantry.set_category("milk", "drinks")
    assert pantry.get_items_in("dairy") == ["cheese"]
    assert pantry.get_items_in("grains") == ["rice"]
    assert pantry.get_items_in("other") == []
    assert pantry.get_categories() == ["drinks", "grains", "dairy"]


def test_categories_follow_the_order_of_their_first_item(pantry):
    pantry.add_item("beans", 4, 20, category="tins")
    pantry.add_item("oats", 1, 40, category="grains")
    pantry.set_category("rice", "grains")
    assert pantry.get_categories() == ["dairy", "grains", "tins"]


def test_a_category_with_no_items_left_disappears(pantry):
    pantry.set_category("milk", "other")
    pantry.set_category("cheese", "other")
    assert pantry.get_categories() == ["other"]
    assert pantry.get_items_in("dairy") == []
    assert pantry.get_category_quantity("dairy") == 0


def test_items_in_a_category_keep_the_order_first_added(pantry):
    pantry.set_category("rice", "dairy")
    assert pantry.get_items_in("dairy") == ["milk", "rice", "cheese"]


def test_category_quantity_follows_the_items(pantry):
    pantry.use_item("milk", 2)
    assert pantry.get_category_quantity("dairy") == 1
    pantry.add_item("cheese", 3, 15)
    assert pantry.get_category_quantity("dairy") == 4
    assert pantry.get_category_quantity("snacks") == 0


def test_an_item_with_nothing_left_stays_in_its_category(pantry):
    pantry.use_item("cheese", 1)
    assert pantry.get_items_in("dairy") == ["milk", "cheese"]
    assert pantry.get_category_quantity("dairy") == 2


@pytest.mark.parametrize("category", BAD_CATEGORIES)
def test_invalid_categories_are_rejected_when_adding(pantry, category):
    before = state(pantry)
    with pytest.raises(ValueError):
        pantry.add_item("milk", 1, 5, category=category)
    with pytest.raises(ValueError):
        pantry.add_item("eggs", 1, 5, category=category)
    assert state(pantry) == before
    assert pantry.get_items() == ["milk", "rice", "cheese"]


@pytest.mark.parametrize("category", BAD_CATEGORIES + [None])
def test_invalid_categories_are_rejected_when_setting(pantry, category):
    before = state(pantry)
    with pytest.raises(ValueError):
        pantry.set_category("milk", category)
    assert state(pantry) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda pan: pan.set_category("eggs", "dairy"),
        lambda pan: pan.get_category("eggs"),
        lambda pan: pan.get_category(None),
        lambda pan: pan.set_category(1, "dairy"),
    ],
)
def test_category_methods_raise_key_error_for_names_that_are_not_items(pantry, call):
    before = state(pantry)
    with pytest.raises(KeyError):
        call(pantry)
    assert state(pantry) == before


def test_an_unknown_item_is_reported_before_a_bad_category(pantry):
    with pytest.raises(KeyError):
        pantry.set_category("eggs", "")


def test_a_bad_quantity_is_reported_before_a_bad_category(pantry):
    # Both are ValueError; the point is that nothing is added either way.
    with pytest.raises(ValueError):
        pantry.add_item("eggs", 0, 5, category="")
    assert pantry.get_items() == ["milk", "rice", "cheese"]
