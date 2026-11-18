"""Hidden tests for the c_recipe_order change (configuration). Never shown to
the writer or the editor.

Usage (with binder.py importable, e.g. in the sandbox):
    python -m pytest changes/c_recipe_order/private/test_recipe_order_new.py
"""

import pytest
from binder import BinderError, RecipeBinder


def make(**kwargs):
    b = RecipeBinder(**kwargs)
    b.add_section("soups", "root")
    b.add_section("mains", "root")
    b.add_section("cold soups", "soups")
    for recipe in ["minestrone", "borscht", "chowder"]:
        b.add_recipe("soups", recipe)
    b.add_recipe("cold soups", "salmorejo")
    b.add_recipe("cold soups", "gazpacho")
    b.add_recipe("mains", "lasagne")
    return b


def tree(b, section="root"):
    return (
        section,
        b.get_recipes(section),
        b.get_recipe_order(section),
        [tree(b, s) for s in b.get_subsections(section)],
    )


# --- settings ---------------------------------------------------------------


def test_every_section_starts_with_the_binder_order():
    b = make()
    assert [b.get_recipe_order(s) for s in ["root", "soups", "mains", "cold soups"]] == ["added"] * 4
    b = make(recipe_order="name")
    assert [b.get_recipe_order(s) for s in ["root", "soups", "mains", "cold soups"]] == ["name"] * 4
    b.add_section("desserts", "root")
    assert b.get_recipe_order("desserts") == "name"


def test_the_binder_order_can_be_given_as_added():
    b = make(recipe_order="added")
    assert b.get_recipes("soups") == ["minestrone", "borscht", "chowder"]


@pytest.mark.parametrize("order", ["alphabetical", "Name", None, ""])
def test_an_invalid_binder_order_is_rejected(order):
    with pytest.raises(ValueError):
        RecipeBinder(recipe_order=order)


def test_set_recipe_order_changes_only_that_section():
    b = make()
    b.set_recipe_order("cold soups", "name")
    assert b.get_recipe_order("cold soups") == "name"
    assert b.get_recipe_order("soups") == "added"
    assert b.get_recipes("cold soups") == ["gazpacho", "salmorejo"]
    assert b.get_recipes("soups") == ["minestrone", "borscht", "chowder"]


@pytest.mark.parametrize("order", ["sorted", "ADDED", None])
def test_an_invalid_section_order_is_rejected(order):
    b = make()
    b.set_recipe_order("soups", "name")
    with pytest.raises(ValueError):
        b.set_recipe_order("soups", order)
    assert b.get_recipe_order("soups") == "name"


def test_sections_not_in_use_raise_key_error():
    b = make()
    b.delete_section("mains")
    for name in ["mains", "salads"]:
        with pytest.raises(KeyError):
            b.get_recipe_order(name)
        with pytest.raises(KeyError):
            b.set_recipe_order(name, "name")


# --- listing ----------------------------------------------------------------


def test_name_order_follows_new_and_removed_recipes():
    b = make()
    b.set_recipe_order("soups", "name")
    b.add_recipe("soups", "bisque")
    b.add_recipe("soups", "pho")
    b.remove_recipe("chowder")
    assert b.get_recipes("soups") == ["bisque", "borscht", "minestrone", "pho"]


def test_switching_back_lists_the_order_they_arrived_in():
    b = make()
    b.set_recipe_order("soups", "name")
    b.add_recipe("soups", "bisque")
    b.set_recipe_order("soups", "added")
    assert b.get_recipes("soups") == ["minestrone", "borscht", "chowder", "bisque"]


def test_name_order_in_a_binder_set_to_name():
    b = RecipeBinder(recipe_order="name")
    for recipe in ["banana bread", "apple pie", "apple crumble", "zucchini cake"]:
        b.add_recipe("root", recipe)
    assert b.get_recipes("root") == ["apple crumble", "apple pie", "banana bread", "zucchini cake"]


def test_get_section_of_and_other_errors_are_unchanged():
    b = make(recipe_order="name")
    assert b.get_section_of("gazpacho") == "cold soups"
    with pytest.raises(BinderError):
        b.add_recipe("mains", "borscht")


# --- delete_section ---------------------------------------------------------


def test_delete_section_appends_recipes_in_the_order_they_arrived():
    b = make()
    b.set_recipe_order("cold soups", "name")
    b.delete_section("cold soups")
    assert b.get_recipes("soups") == ["minestrone", "borscht", "chowder", "salmorejo", "gazpacho"]


def test_a_parent_set_to_name_lists_the_recipes_it_received_sorted():
    b = make()
    b.set_recipe_order("soups", "name")
    b.delete_section("cold soups")
    assert b.get_recipes("soups") == ["borscht", "chowder", "gazpacho", "minestrone", "salmorejo"]
    b.set_recipe_order("soups", "added")
    assert b.get_recipes("soups") == ["minestrone", "borscht", "chowder", "salmorejo", "gazpacho"]


def test_set_recipe_order_changes_no_recipes_or_sections():
    b = make()
    before = [(s, sorted(b.get_recipes(s)), b.get_subsections(s)) for s in ["root", "soups"]]
    b.set_recipe_order("soups", "name")
    b.set_recipe_order("root", "name")
    assert [(s, sorted(b.get_recipes(s)), b.get_subsections(s)) for s in ["root", "soups"]] == before
