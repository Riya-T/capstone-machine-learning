"""Hidden tests for the c_queries change (query). Never shown to the writer
or the editor.

Usage (with binder.py importable, e.g. in the sandbox):
    python -m pytest changes/c_queries/private/test_queries_new.py
"""

import pytest
from binder import RecipeBinder


@pytest.fixture
def binder():
    b = RecipeBinder()
    b.add_section("soups", "root")
    b.add_section("mains", "root")
    b.add_section("desserts", "root")
    b.add_section("cold soups", "soups")
    b.add_section("fish", "mains")
    b.add_section("chilled", "cold soups")
    b.add_recipe("soups", "minestrone")
    b.add_recipe("cold soups", "gazpacho")
    b.add_recipe("soups", "borscht")
    b.add_recipe("chilled", "vichyssoise")
    b.add_recipe("mains", "lasagne")
    b.add_recipe("fish", "paella")
    b.add_recipe("root", "toast")
    return b


def tree(b, section="root"):
    return (section, b.get_recipes(section), [tree(b, s) for s in b.get_subsections(section)])


# --- get_all_recipes --------------------------------------------------------


def test_all_recipes_of_the_whole_binder(binder):
    assert binder.get_all_recipes("root") == [
        "toast",
        "minestrone",
        "borscht",
        "gazpacho",
        "vichyssoise",
        "lasagne",
        "paella",
    ]


def test_all_recipes_of_a_branch(binder):
    assert binder.get_all_recipes("soups") == ["minestrone", "borscht", "gazpacho", "vichyssoise"]
    assert binder.get_all_recipes("mains") == ["lasagne", "paella"]
    assert binder.get_all_recipes("chilled") == ["vichyssoise"]


def test_all_recipes_of_an_empty_section(binder):
    assert binder.get_all_recipes("desserts") == []
    binder.add_section("cakes", "desserts")
    binder.add_section("pies", "desserts")
    binder.add_recipe("pies", "apple pie")
    assert binder.get_all_recipes("desserts") == ["apple pie"]


def test_a_whole_branch_comes_before_the_next_sibling(binder):
    binder.add_section("hot soups", "soups")
    binder.add_recipe("hot soups", "chowder")
    assert binder.get_all_recipes("soups") == [
        "minestrone",
        "borscht",
        "gazpacho",
        "vichyssoise",
        "chowder",
    ]


def test_all_recipes_follow_moves_deletes_and_removals(binder):
    binder.move_section("fish", "soups")
    binder.remove_recipe("borscht")
    binder.delete_section("cold soups")
    assert binder.get_all_recipes("soups") == ["minestrone", "gazpacho", "paella", "vichyssoise"]
    assert binder.get_all_recipes("mains") == ["lasagne"]


def test_all_recipes_of_a_new_binder_is_empty():
    assert RecipeBinder().get_all_recipes("root") == []


# --- get_path ---------------------------------------------------------------


def test_paths_of_sections_at_each_depth(binder):
    assert binder.get_path("root") == ["root"]
    assert binder.get_path("desserts") == ["root", "desserts"]
    assert binder.get_path("fish") == ["root", "mains", "fish"]
    assert binder.get_path("chilled") == ["root", "soups", "cold soups", "chilled"]


def test_paths_follow_moves_and_deletes(binder):
    binder.move_section("cold soups", "fish")
    assert binder.get_path("chilled") == ["root", "mains", "fish", "cold soups", "chilled"]
    binder.delete_section("mains")
    assert binder.get_path("chilled") == ["root", "fish", "cold soups", "chilled"]
    binder.delete_section("cold soups")
    assert binder.get_path("chilled") == ["root", "fish", "chilled"]


# --- errors and side effects ------------------------------------------------


def test_sections_not_in_use_raise_key_error(binder):
    binder.delete_section("desserts")
    for name in ["desserts", "salads"]:
        with pytest.raises(KeyError):
            binder.get_all_recipes(name)
        with pytest.raises(KeyError):
            binder.get_path(name)


def test_the_queries_change_nothing(binder):
    before = tree(binder)
    binder.get_all_recipes("root")
    binder.get_path("chilled")
    assert tree(binder) == before
