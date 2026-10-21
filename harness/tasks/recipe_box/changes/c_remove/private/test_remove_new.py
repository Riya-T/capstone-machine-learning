"""Hidden tests for the c_remove change (removing ingredients and undoing
additions). Never shown to the writer or the editor.

Usage (with recipes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_remove/private/test_remove_new.py
"""

import pytest
from recipes import RecipeBox, RecipeError


@pytest.fixture
def box():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4)
    rb.add_recipe("omelette", 1)
    rb.add_ingredient("pancakes", "flour", 200)
    rb.add_ingredient("pancakes", "egg", 2)
    rb.add_ingredient("pancakes", "milk", 300)
    rb.add_ingredient("omelette", "egg", 3)
    return rb


def state(rb):
    return {r: (rb.get_servings(r), rb.get_ingredients(r)) for r in rb.get_recipes()}


# --- remove_ingredient ------------------------------------------------------


def test_removing_keeps_the_other_ingredients_in_order(box):
    box.remove_ingredient("pancakes", "egg")
    assert box.get_ingredients("pancakes") == [("flour", 200), ("milk", 300)]
    assert box.get_ingredients("omelette") == [("egg", 3)]


def test_a_removed_ingredient_added_again_goes_to_the_end(box):
    box.remove_ingredient("pancakes", "flour")
    box.add_ingredient("pancakes", "flour", 100)
    assert box.get_ingredients("pancakes") == [("egg", 2), ("milk", 300), ("flour", 100)]


def test_removing_changes_the_shopping_list(box):
    box.remove_ingredient("pancakes", "egg")
    assert box.get_shopping_list(["pancakes", "omelette"]) == [
        ("flour", 200),
        ("milk", 300),
        ("egg", 3),
    ]


@pytest.mark.parametrize("ingredient", ["butter", "", None, 3])
def test_removing_an_ingredient_the_recipe_lacks_changes_nothing(box, ingredient):
    before = state(box)
    with pytest.raises(RecipeError):
        box.remove_ingredient("pancakes", ingredient)
    assert state(box) == before


def test_removing_from_an_unknown_recipe_raises_key_error(box):
    before = state(box)
    with pytest.raises(KeyError):
        box.remove_ingredient("soup", "flour")
    with pytest.raises(KeyError):
        box.remove_ingredient(None, "butter")
    assert state(box) == before


# --- undo_add ---------------------------------------------------------------


def test_undo_removes_an_ingredient_created_by_the_last_addition(box):
    box.undo_add("pancakes")
    assert box.get_ingredients("pancakes") == [("flour", 200), ("egg", 2)]


def test_undo_restores_the_previous_quantity_in_place(box):
    box.add_ingredient("pancakes", "flour", 50)
    assert box.get_ingredients("pancakes") == [("flour", 250), ("egg", 2), ("milk", 300)]
    box.undo_add("pancakes")
    assert box.get_ingredients("pancakes") == [("flour", 200), ("egg", 2), ("milk", 300)]


def test_undo_steps_back_through_every_addition(box):
    box.add_ingredient("pancakes", "egg", 1)
    box.undo_add("pancakes")
    box.undo_add("pancakes")
    box.undo_add("pancakes")
    assert box.get_ingredients("pancakes") == [("flour", 200)]
    box.undo_add("pancakes")
    assert box.get_ingredients("pancakes") == []
    with pytest.raises(RecipeError):
        box.undo_add("pancakes")


def test_undo_only_touches_the_named_recipe(box):
    box.undo_add("omelette")
    assert box.get_ingredients("omelette") == []
    assert box.get_ingredients("pancakes") == [("flour", 200), ("egg", 2), ("milk", 300)]


def test_an_addition_after_an_undo_can_be_undone_again(box):
    box.undo_add("pancakes")
    box.add_ingredient("pancakes", "butter", 20)
    assert box.get_ingredients("pancakes") == [("flour", 200), ("egg", 2), ("butter", 20)]
    box.undo_add("pancakes")
    assert box.get_ingredients("pancakes") == [("flour", 200), ("egg", 2)]


def test_undo_with_nothing_to_reverse_changes_nothing(box):
    box.undo_add("omelette")
    before = state(box)
    with pytest.raises(RecipeError):
        box.undo_add("omelette")
    assert state(box) == before


def test_undo_on_an_unknown_recipe_raises_key_error(box):
    before = state(box)
    with pytest.raises(KeyError):
        box.undo_add("soup")
    with pytest.raises(KeyError):
        box.undo_add(3)
    assert state(box) == before


def test_removing_discards_the_undo_history(box):
    box.remove_ingredient("pancakes", "egg")
    before = state(box)
    with pytest.raises(RecipeError):
        box.undo_add("pancakes")
    assert state(box) == before
    box.add_ingredient("pancakes", "sugar", 30)
    box.undo_add("pancakes")
    assert box.get_ingredients("pancakes") == [("flour", 200), ("milk", 300)]
    with pytest.raises(RecipeError):
        box.undo_add("pancakes")


def test_a_failed_addition_leaves_nothing_to_undo(box):
    box.add_recipe("water", 1)
    with pytest.raises(ValueError):
        box.add_ingredient("water", "ice", 0)
    with pytest.raises(RecipeError):
        box.undo_add("water")
