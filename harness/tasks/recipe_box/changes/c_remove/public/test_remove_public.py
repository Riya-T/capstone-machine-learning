"""Public checks for the c_remove change (removing ingredients and undoing
additions). Shown to the editor, never to the writer.

Usage (with recipes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_remove/public/test_remove_public.py
"""

import pytest
from recipes import RecipeBox, RecipeError


def test_remove_ingredient_drops_it_entirely():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4)
    rb.add_ingredient("pancakes", "flour", 200)
    rb.add_ingredient("pancakes", "egg", 2)
    rb.remove_ingredient("pancakes", "flour")
    assert rb.get_ingredients("pancakes") == [("egg", 2)]
    with pytest.raises(RecipeError):
        rb.remove_ingredient("pancakes", "flour")


def test_undo_add_reverses_the_latest_addition():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4)
    rb.add_ingredient("pancakes", "flour", 200)
    rb.add_ingredient("pancakes", "egg", 2)
    rb.add_ingredient("pancakes", "flour", 50)
    rb.undo_add("pancakes")
    assert rb.get_ingredients("pancakes") == [("flour", 200), ("egg", 2)]
    rb.undo_add("pancakes")
    assert rb.get_ingredients("pancakes") == [("flour", 200)]


def test_undo_with_nothing_to_reverse_raises():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4)
    with pytest.raises(RecipeError):
        rb.undo_add("pancakes")
