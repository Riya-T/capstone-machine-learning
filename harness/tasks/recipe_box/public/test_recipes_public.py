"""Public checks for recipes.py.

Usage (with recipes.py importable, e.g. in the sandbox):
    python -m pytest public/test_recipes_public.py
"""

import pytest
from recipes import RecipeBox


@pytest.fixture
def box():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4)
    rb.add_recipe("omelette", 1)
    return rb


def test_a_new_recipe_has_servings_and_no_ingredients(box):
    assert box.get_servings("pancakes") == 4
    assert box.get_ingredients("pancakes") == []
    assert box.get_recipes() == ["pancakes", "omelette"]


def test_ingredients_are_listed_in_the_order_first_added(box):
    box.add_ingredient("pancakes", "flour", 200)
    box.add_ingredient("pancakes", "milk", 300)
    box.add_ingredient("pancakes", "egg", 2)
    assert box.get_ingredients("pancakes") == [("flour", 200), ("milk", 300), ("egg", 2)]


def test_adding_an_ingredient_again_adds_to_its_quantity(box):
    box.add_ingredient("pancakes", "flour", 200)
    box.add_ingredient("pancakes", "milk", 300)
    box.add_ingredient("pancakes", "flour", 50)
    assert box.get_ingredients("pancakes") == [("flour", 250), ("milk", 300)]


def test_shopping_list_totals_over_several_recipes(box):
    box.add_ingredient("pancakes", "flour", 200)
    box.add_ingredient("pancakes", "egg", 2)
    box.add_ingredient("omelette", "egg", 3)
    box.add_ingredient("omelette", "butter", 10)
    assert box.get_shopping_list(["pancakes", "omelette"]) == [
        ("flour", 200),
        ("egg", 5),
        ("butter", 10),
    ]
    assert box.get_shopping_list([]) == []


def test_quantities_must_be_positive(box):
    with pytest.raises(ValueError):
        box.add_ingredient("pancakes", "flour", 0)
    with pytest.raises(ValueError):
        box.add_ingredient("pancakes", "flour", -5)
    assert box.get_ingredients("pancakes") == []


def test_unknown_recipe_raises_key_error(box):
    with pytest.raises(KeyError):
        box.get_servings("soup")
    with pytest.raises(KeyError):
        box.add_ingredient("soup", "water", 500)
