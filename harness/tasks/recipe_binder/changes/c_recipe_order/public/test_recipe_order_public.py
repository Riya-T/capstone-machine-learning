"""Public checks for the c_recipe_order change (configuration). Shown to the
editor, never to the writer.

Usage (with binder.py importable, e.g. in the sandbox):
    python -m pytest changes/c_recipe_order/public/test_recipe_order_public.py
"""

from binder import RecipeBinder


def make(**kwargs):
    b = RecipeBinder(**kwargs)
    b.add_section("soups", "root")
    for recipe in ["minestrone", "borscht", "chowder"]:
        b.add_recipe("soups", recipe)
    return b


def test_recipes_are_listed_as_added_by_default():
    b = make()
    assert b.get_recipe_order("soups") == "added"
    assert b.get_recipes("soups") == ["minestrone", "borscht", "chowder"]


def test_a_section_set_to_name_lists_its_recipes_sorted():
    b = make()
    b.set_recipe_order("soups", "name")
    assert b.get_recipes("soups") == ["borscht", "chowder", "minestrone"]


def test_the_binder_sets_the_order_of_root_and_new_sections():
    b = make(recipe_order="name")
    assert b.get_recipe_order("root") == "name"
    assert b.get_recipes("soups") == ["borscht", "chowder", "minestrone"]
