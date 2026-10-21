"""Public checks for the c_categories change (recipe categories). Shown to
the editor, never to the writer.

Usage (with recipes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_categories/public/test_categories_public.py
"""

import pytest
from recipes import RecipeBox


def test_recipes_can_be_listed_by_category():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4, category="breakfast")
    rb.add_recipe("brownie", 8, category="dessert")
    rb.add_recipe("omelette", 1, category="breakfast")
    assert rb.get_recipes() == ["pancakes", "brownie", "omelette"]
    assert rb.get_recipes(category="breakfast") == ["pancakes", "omelette"]
    assert rb.get_recipes(category="soup") == []
    assert rb.get_categories() == ["breakfast", "dessert"]


def test_the_default_category_and_moving_a_recipe():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4)
    assert rb.get_category("pancakes") == "uncategorized"
    rb.set_category("pancakes", "breakfast")
    assert rb.get_category("pancakes") == "breakfast"
    assert rb.get_categories() == ["breakfast"]


def test_an_invalid_category_adds_no_recipe():
    rb = RecipeBox()
    with pytest.raises(ValueError):
        rb.add_recipe("pancakes", 4, category="")
    assert rb.get_recipes() == []
