"""Hidden tests for the initial recipe_binder spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with binder.py importable, e.g. in the sandbox):
    python -m pytest private/test_binder_initial.py
"""

import pytest
from binder import BinderError, RecipeBinder


@pytest.fixture
def binder():
    b = RecipeBinder()
    b.add_section("soups", "root")
    b.add_section("mains", "root")
    b.add_section("desserts", "root")
    b.add_section("cold soups", "soups")
    b.add_section("fish", "mains")
    b.add_recipe("soups", "minestrone")
    b.add_recipe("soups", "borscht")
    b.add_recipe("cold soups", "gazpacho")
    b.add_recipe("mains", "lasagne")
    b.add_recipe("fish", "paella")
    return b


def tree(b, section="root"):
    """The whole binder below `section`, to check that a failed call changed
    nothing."""
    return (
        section,
        list(b.get_recipes(section)),
        [tree(b, s) for s in list(b.get_subsections(section))],
    )


# --- sections ---------------------------------------------------------------


def test_a_new_binder_has_only_an_empty_root():
    b = RecipeBinder()
    assert b.get_subsections("root") == []
    assert b.get_recipes("root") == []


def test_sections_are_listed_in_the_order_added(binder):
    binder.add_section("cakes", "desserts")
    binder.add_section("ices", "desserts")
    binder.add_section("pies", "desserts")
    assert binder.get_subsections("desserts") == ["cakes", "ices", "pies"]
    assert binder.get_subsections("root") == ["soups", "mains", "desserts"]
    assert binder.get_subsections("cakes") == []


@pytest.mark.parametrize("name", ["soups", "fish", "root"])
def test_adding_a_name_in_use_is_rejected(binder, name):
    before = tree(binder)
    with pytest.raises(BinderError):
        binder.add_section(name, "desserts")
    assert tree(binder) == before


SECTION_CALLS = [
    lambda b, s: b.add_section("new", s),
    lambda b, s: b.add_recipe(s, "stew"),
    lambda b, s: b.move_section(s, "root"),
    lambda b, s: b.move_section("fish", s),
    lambda b, s: b.delete_section(s),
    lambda b, s: b.get_recipes(s),
    lambda b, s: b.get_subsections(s),
]


@pytest.mark.parametrize("call", SECTION_CALLS)
def test_sections_that_were_never_added_raise_key_error(binder, call):
    before = tree(binder)
    with pytest.raises(KeyError):
        call(binder, "salads")
    assert tree(binder) == before


@pytest.mark.parametrize("call", SECTION_CALLS)
def test_a_deleted_section_is_not_in_use(binder, call):
    binder.delete_section("desserts")
    before = tree(binder)
    with pytest.raises(KeyError):
        call(binder, "desserts")
    assert tree(binder) == before


# --- recipes ----------------------------------------------------------------


def test_recipes_are_listed_in_the_order_added(binder):
    binder.add_recipe("desserts", "tiramisu")
    binder.add_recipe("desserts", "flan")
    binder.add_recipe("root", "toast")
    assert binder.get_recipes("desserts") == ["tiramisu", "flan"]
    assert binder.get_recipes("root") == ["toast"]
    assert binder.get_recipes("soups") == ["minestrone", "borscht"]
    assert binder.get_section_of("flan") == "desserts"
    assert binder.get_section_of("toast") == "root"


def test_a_recipe_in_the_binder_cannot_be_added_again(binder):
    before = tree(binder)
    with pytest.raises(BinderError):
        binder.add_recipe("desserts", "paella")
    with pytest.raises(BinderError):
        binder.add_recipe("soups", "minestrone")
    assert tree(binder) == before


def test_remove_recipe_keeps_the_order_of_the_others(binder):
    binder.add_recipe("soups", "chowder")
    binder.remove_recipe("borscht")
    assert binder.get_recipes("soups") == ["minestrone", "chowder"]
    with pytest.raises(KeyError):
        binder.get_section_of("borscht")


def test_a_removed_recipe_can_be_added_again(binder):
    binder.remove_recipe("minestrone")
    binder.add_recipe("mains", "minestrone")
    assert binder.get_recipes("mains") == ["lasagne", "minestrone"]
    assert binder.get_section_of("minestrone") == "mains"


def test_recipes_not_in_the_binder_raise_key_error(binder):
    binder.remove_recipe("paella")
    before = tree(binder)
    for recipe in ["paella", "risotto"]:
        with pytest.raises(KeyError):
            binder.remove_recipe(recipe)
        with pytest.raises(KeyError):
            binder.get_section_of(recipe)
    assert tree(binder) == before


# --- moving sections --------------------------------------------------------


def test_move_section_puts_it_last_under_the_new_parent(binder):
    binder.add_section("salads", "desserts")
    binder.move_section("fish", "desserts")
    assert binder.get_subsections("desserts") == ["salads", "fish"]
    assert binder.get_subsections("mains") == []
    assert binder.get_recipes("fish") == ["paella"]
    assert binder.get_section_of("paella") == "fish"


def test_move_section_takes_everything_below_it(binder):
    binder.add_section("chilled", "cold soups")
    binder.add_recipe("chilled", "vichyssoise")
    binder.move_section("soups", "fish")
    assert binder.get_subsections("root") == ["mains", "desserts"]
    assert tree(binder, "fish") == (
        "fish",
        ["paella"],
        [("soups", ["minestrone", "borscht"], [
            ("cold soups", ["gazpacho"], [("chilled", ["vichyssoise"], [])]),
        ])],
    )


def test_a_section_can_be_moved_up_to_root(binder):
    binder.move_section("cold soups", "root")
    assert binder.get_subsections("root") == ["soups", "mains", "desserts", "cold soups"]
    assert binder.get_subsections("soups") == []
    binder.move_section("soups", "cold soups")
    assert binder.get_subsections("cold soups") == ["soups"]


def test_a_moved_section_leaves_its_old_parent_and_the_rest_keep_their_order(binder):
    binder.add_section("salads", "root")
    binder.move_section("mains", "desserts")
    assert binder.get_subsections("root") == ["soups", "desserts", "salads"]
    assert binder.get_subsections("desserts") == ["mains"]
    binder.move_section("soups", "desserts")
    assert binder.get_subsections("desserts") == ["mains", "soups"]
    assert binder.get_subsections("root") == ["desserts", "salads"]


# --- deleting sections ------------------------------------------------------


def test_delete_section_gives_its_recipes_to_its_parent(binder):
    binder.add_recipe("root", "toast")
    binder.delete_section("soups")
    assert binder.get_recipes("root") == ["toast", "minestrone", "borscht"]
    assert binder.get_section_of("borscht") == "root"
    assert binder.get_subsections("root") == ["mains", "desserts", "cold soups"]
    assert binder.get_recipes("cold soups") == ["gazpacho"]


def test_delete_section_gives_its_subsections_to_its_parent_in_order(binder):
    binder.add_section("trout", "fish")
    binder.add_section("pasta", "mains")
    binder.add_section("meat", "fish")
    binder.add_recipe("meat", "steak")
    binder.delete_section("fish")
    assert binder.get_subsections("mains") == ["pasta", "trout", "meat"]
    assert binder.get_recipes("mains") == ["lasagne", "paella"]
    assert binder.get_section_of("paella") == "mains"
    assert binder.get_recipes("meat") == ["steak"]


def test_sections_moved_up_by_a_delete_can_be_used_as_before(binder):
    binder.delete_section("soups")
    binder.add_recipe("cold soups", "salmorejo")
    binder.move_section("cold soups", "desserts")
    assert binder.get_recipes("cold soups") == ["gazpacho", "salmorejo"]
    assert binder.get_subsections("desserts") == ["cold soups"]
    binder.delete_section("desserts")
    assert binder.get_subsections("root") == ["mains", "cold soups"]


def test_deleting_an_empty_section(binder):
    binder.delete_section("desserts")
    assert binder.get_subsections("root") == ["soups", "mains"]
    assert binder.get_recipes("root") == []


def test_deleting_a_section_deep_in_the_tree(binder):
    binder.add_section("chilled", "cold soups")
    binder.add_recipe("chilled", "vichyssoise")
    binder.delete_section("cold soups")
    assert binder.get_subsections("soups") == ["chilled"]
    assert binder.get_recipes("soups") == ["minestrone", "borscht", "gazpacho"]
    assert binder.get_section_of("gazpacho") == "soups"
    assert binder.get_section_of("vichyssoise") == "chilled"


def test_the_root_section_cannot_be_moved_or_deleted(binder):
    before = tree(binder)
    with pytest.raises(BinderError):
        binder.delete_section("root")
    with pytest.raises(BinderError):
        binder.move_section("root", "desserts")
    assert tree(binder) == before


# --- general ----------------------------------------------------------------


def test_binders_do_not_share_sections():
    first, second = RecipeBinder(), RecipeBinder()
    first.add_section("soups", "root")
    first.add_recipe("soups", "minestrone")
    assert second.get_subsections("root") == []
    second.add_section("soups", "root")
    second.add_recipe("soups", "minestrone")
    assert first.get_recipes("soups") == ["minestrone"]
