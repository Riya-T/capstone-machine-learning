"""Hidden tests for the c_categories change (recipe categories). Never shown
to the writer or the editor.

Usage (with recipes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_categories/private/test_categories_new.py
"""

import pytest
from recipes import RecipeBox, RecipeError


@pytest.fixture
def box():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4, category="breakfast")
    rb.add_recipe("brownie", 8, category="dessert")
    rb.add_recipe("omelette", 1, category="breakfast")
    rb.add_recipe("water", 1)
    rb.add_ingredient("pancakes", "flour", 200)
    rb.add_ingredient("omelette", "egg", 3)
    return rb


def state(rb):
    return {
        r: (rb.get_servings(r), rb.get_category(r), rb.get_ingredients(r))
        for r in rb.get_recipes()
    }


def test_each_recipe_knows_its_category(box):
    assert box.get_category("pancakes") == "breakfast"
    assert box.get_category("brownie") == "dessert"
    assert box.get_category("water") == "uncategorized"


def test_listing_without_a_category_is_unchanged(box):
    assert box.get_recipes() == ["pancakes", "brownie", "omelette", "water"]
    assert box.get_recipes(category=None) == ["pancakes", "brownie", "omelette", "water"]


def test_listing_by_category_keeps_the_added_order(box):
    assert box.get_recipes(category="breakfast") == ["pancakes", "omelette"]
    assert box.get_recipes(category="dessert") == ["brownie"]
    assert box.get_recipes(category="uncategorized") == ["water"]
    assert box.get_recipes(category="soup") == []


def test_categories_follow_first_appearance_in_the_recipe_list(box):
    assert box.get_categories() == ["breakfast", "dessert", "uncategorized"]


def test_moving_a_recipe_updates_every_listing(box):
    box.set_category("brownie", "breakfast")
    assert box.get_category("brownie") == "breakfast"
    assert box.get_recipes(category="breakfast") == ["pancakes", "brownie", "omelette"]
    assert box.get_recipes(category="dessert") == []
    assert box.get_categories() == ["breakfast", "uncategorized"]


def test_an_abandoned_category_can_be_used_again(box):
    box.set_category("brownie", "snack")
    assert box.get_categories() == ["breakfast", "snack", "uncategorized"]
    box.set_category("water", "dessert")
    assert box.get_categories() == ["breakfast", "snack", "dessert"]


@pytest.mark.parametrize("category", ["", None, 3])
def test_invalid_categories_are_rejected_when_adding(box, category):
    before = state(box)
    with pytest.raises(ValueError):
        box.add_recipe("soup", 2, category=category)
    assert state(box) == before


@pytest.mark.parametrize("category", ["", None, 3])
def test_invalid_categories_are_rejected_when_moving(box, category):
    before = state(box)
    with pytest.raises(ValueError):
        box.set_category("pancakes", category)
    assert state(box) == before


def test_a_bad_category_is_reported_before_a_duplicate_name(box):
    before = state(box)
    with pytest.raises(ValueError):
        box.add_recipe("pancakes", 4, category="")
    assert state(box) == before


def test_a_duplicate_name_with_a_valid_category_is_still_rejected(box):
    before = state(box)
    with pytest.raises(RecipeError):
        box.add_recipe("pancakes", 4, category="dessert")
    assert state(box) == before


def test_unknown_recipes_raise_key_error_in_category_methods(box):
    before = state(box)
    with pytest.raises(KeyError):
        box.get_category("soup")
    with pytest.raises(KeyError):
        box.set_category("soup", "dinner")
    with pytest.raises(KeyError):
        box.set_category(None, "")
    assert state(box) == before


def test_cookable_can_be_filtered_by_category(box):
    box.stock("flour", 200)
    assert box.get_cookable() == ["pancakes", "brownie", "water"]
    assert box.get_cookable(category="breakfast") == ["pancakes"]
    assert box.get_cookable(category="dessert") == ["brownie"]
    assert box.get_cookable(category="soup") == []
    box.set_category("water", "breakfast")
    assert box.get_cookable(category="breakfast") == ["pancakes", "water"]


def test_the_shopping_list_ignores_categories(box):
    assert box.get_shopping_list(["pancakes", "omelette", "brownie"]) == [
        ("flour", 200),
        ("egg", 3),
    ]
