"""Public checks for the c_pantry change (pantry and cookable recipes). Shown
to the editor, never to the writer.

Usage (with recipes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_pantry/public/test_pantry_public.py
"""

import pytest
from recipes import RecipeBox, RecipeError


def test_missing_lists_the_shortfall_per_ingredient():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4)
    rb.add_ingredient("pancakes", "flour", 200)
    rb.add_ingredient("pancakes", "egg", 2)
    rb.stock("flour", 150)
    assert rb.get_missing("pancakes") == [("flour", 50), ("egg", 2)]
    assert rb.get_cookable() == []


def test_cooking_takes_ingredients_from_the_pantry():
    rb = RecipeBox()
    rb.add_recipe("omelette", 1)
    rb.add_ingredient("omelette", "egg", 3)
    rb.stock("egg", 5)
    rb.stock("salt", 10)
    assert rb.get_cookable() == ["omelette"]
    rb.cook("omelette")
    assert rb.get_pantry() == [("egg", 2), ("salt", 10)]
    assert rb.get_missing("omelette") == [("egg", 1)]
    with pytest.raises(RecipeError):
        rb.cook("omelette")
