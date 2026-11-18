"""Public checks for binder.py.

Usage (with binder.py importable, e.g. in the sandbox):
    python -m pytest public/test_binder_public.py
"""

import pytest
from binder import BinderError, RecipeBinder


@pytest.fixture
def binder():
    b = RecipeBinder()
    b.add_section("soups", "root")
    b.add_section("desserts", "root")
    return b


def test_sections_and_recipes_are_listed_in_the_order_added(binder):
    binder.add_section("cold soups", "soups")
    binder.add_recipe("soups", "minestrone")
    binder.add_recipe("soups", "borscht")
    assert binder.get_subsections("root") == ["soups", "desserts"]
    assert binder.get_subsections("soups") == ["cold soups"]
    assert binder.get_recipes("soups") == ["minestrone", "borscht"]
    assert binder.get_section_of("borscht") == "soups"
    assert binder.get_recipes("root") == []


def test_a_recipe_name_can_only_be_used_once(binder):
    binder.add_recipe("soups", "minestrone")
    with pytest.raises(BinderError):
        binder.add_recipe("desserts", "minestrone")
    assert binder.get_recipes("desserts") == []


def test_delete_section_gives_its_contents_to_its_parent(binder):
    binder.add_recipe("root", "toast")
    binder.add_section("cold soups", "soups")
    binder.add_recipe("soups", "minestrone")
    binder.delete_section("soups")
    assert binder.get_recipes("root") == ["toast", "minestrone"]
    assert binder.get_subsections("root") == ["desserts", "cold soups"]
    with pytest.raises(KeyError):
        binder.get_recipes("soups")


def test_move_section_takes_everything_below_it(binder):
    binder.add_section("cold soups", "soups")
    binder.add_recipe("cold soups", "gazpacho")
    binder.move_section("soups", "desserts")
    assert binder.get_subsections("root") == ["desserts"]
    assert binder.get_subsections("desserts") == ["soups"]
    assert binder.get_subsections("soups") == ["cold soups"]
    assert binder.get_recipes("cold soups") == ["gazpacho"]


def test_the_root_section_cannot_be_moved(binder):
    with pytest.raises(BinderError):
        binder.move_section("root", "soups")
    assert binder.get_subsections("root") == ["soups", "desserts"]
    assert binder.get_subsections("soups") == []


def test_the_root_section_cannot_be_deleted(binder):
    with pytest.raises(BinderError):
        binder.delete_section("root")
    assert binder.get_subsections("root") == ["soups", "desserts"]
