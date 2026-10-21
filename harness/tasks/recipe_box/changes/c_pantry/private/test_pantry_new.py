"""Hidden tests for the c_pantry change (pantry and cookable recipes). Never
shown to the writer or the editor.

Usage (with recipes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_pantry/private/test_pantry_new.py
"""

import pytest
from recipes import RecipeBox, RecipeError


@pytest.fixture
def box():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4)
    rb.add_recipe("omelette", 1)
    rb.add_recipe("water", 1)
    rb.add_ingredient("pancakes", "flour", 200)
    rb.add_ingredient("pancakes", "egg", 2)
    rb.add_ingredient("omelette", "egg", 3)
    rb.add_ingredient("omelette", "cheese", 50)
    return rb


def state(rb):
    recipes = {r: (rb.get_servings(r), rb.get_ingredients(r)) for r in rb.get_recipes()}
    return recipes, rb.get_pantry()


def test_the_pantry_starts_empty(box):
    assert box.get_pantry() == []
    assert box.get_missing("pancakes") == [("flour", 200), ("egg", 2)]


def test_stocking_adds_up_and_keeps_first_stocked_order(box):
    box.stock("egg", 2)
    box.stock("flour", 100)
    box.stock("egg", 4)
    assert box.get_pantry() == [("egg", 6), ("flour", 100)]


def test_a_recipe_without_ingredients_is_always_cookable(box):
    assert box.get_missing("water") == []
    assert box.get_cookable() == ["water"]


def test_cookable_follows_the_order_recipes_were_added(box):
    box.stock("egg", 5)
    box.stock("cheese", 50)
    assert box.get_cookable() == ["omelette", "water"]
    box.stock("flour", 200)
    assert box.get_cookable() == ["pancakes", "omelette", "water"]


def test_exactly_enough_stock_counts_as_covered(box):
    box.stock("flour", 200)
    box.stock("egg", 2)
    assert box.get_missing("pancakes") == []
    assert box.get_missing("omelette") == [("egg", 1), ("cheese", 50)]


def test_cooking_reduces_the_pantry_but_not_the_recipe(box):
    box.stock("egg", 5)
    box.stock("cheese", 60)
    box.cook("omelette")
    assert box.get_pantry() == [("egg", 2), ("cheese", 10)]
    assert box.get_ingredients("omelette") == [("egg", 3), ("cheese", 50)]
    assert box.get_servings("omelette") == 1


def test_an_ingredient_used_up_stays_in_the_pantry_at_zero(box):
    box.stock("egg", 3)
    box.stock("cheese", 50)
    box.cook("omelette")
    assert box.get_pantry() == [("egg", 0), ("cheese", 0)]
    assert box.get_missing("omelette") == [("egg", 3), ("cheese", 50)]


def test_cooking_a_recipe_with_missing_ingredients_changes_nothing(box):
    box.stock("egg", 10)
    before = state(box)
    with pytest.raises(RecipeError):
        box.cook("pancakes")
    assert state(box) == before


def test_cooking_one_recipe_can_make_another_uncookable(box):
    box.stock("flour", 200)
    box.stock("egg", 4)
    box.stock("cheese", 50)
    assert box.get_cookable() == ["pancakes", "omelette", "water"]
    box.cook("pancakes")
    assert box.get_cookable() == ["water"]
    assert box.get_missing("omelette") == [("egg", 1)]


@pytest.mark.parametrize("ingredient", ["", None, 3])
def test_invalid_pantry_ingredients_are_rejected(box, ingredient):
    with pytest.raises(ValueError):
        box.stock(ingredient, 10)
    assert box.get_pantry() == []


@pytest.mark.parametrize("quantity", [0, -5, 1.5, "10", None])
def test_invalid_pantry_quantities_are_rejected(box, quantity):
    with pytest.raises(ValueError):
        box.stock("flour", quantity)
    assert box.get_pantry() == []


def test_a_bad_ingredient_is_reported_before_a_bad_pantry_quantity(box):
    with pytest.raises(ValueError):
        box.stock("", 0)


@pytest.mark.parametrize(
    "call",
    [
        lambda rb: rb.get_missing("soup"),
        lambda rb: rb.cook("soup"),
        lambda rb: rb.get_missing(None),
        lambda rb: rb.cook(3),
    ],
)
def test_unknown_recipes_raise_key_error_in_pantry_methods(box, call):
    box.stock("egg", 1)
    before = state(box)
    with pytest.raises(KeyError):
        call(box)
    assert state(box) == before


def test_stocking_unused_ingredients_is_fine(box):
    box.stock("saffron", 1)
    assert box.get_pantry() == [("saffron", 1)]
    assert box.get_cookable() == ["water"]
