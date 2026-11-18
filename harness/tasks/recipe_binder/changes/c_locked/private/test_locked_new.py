"""Hidden tests for the c_locked change (state flag). Never shown to the
writer or the editor.

Usage (with binder.py importable, e.g. in the sandbox):
    python -m pytest changes/c_locked/private/test_locked_new.py
"""

import pytest
from binder import BinderError, RecipeBinder, SectionLocked


@pytest.fixture
def binder():
    b = RecipeBinder()
    b.add_section("soups", "root")
    b.add_section("mains", "root")
    b.add_section("cold soups", "soups")
    b.add_recipe("soups", "minestrone")
    b.add_recipe("soups", "borscht")
    b.add_recipe("cold soups", "gazpacho")
    b.add_recipe("mains", "lasagne")
    return b


def tree(b, section="root"):
    return (
        section,
        b.get_recipes(section),
        b.get_locked(section),
        [tree(b, s) for s in b.get_subsections(section)],
    )


# --- the flag ---------------------------------------------------------------


def test_section_locked_is_a_binder_error():
    assert issubclass(SectionLocked, BinderError)


def test_every_section_starts_unlocked(binder):
    for section in ["root", "soups", "mains", "cold soups"]:
        assert binder.get_locked(section) is False


def test_a_section_can_be_locked_and_unlocked(binder):
    binder.set_locked("soups", True)
    assert binder.get_locked("soups") is True
    assert binder.get_locked("cold soups") is False
    assert binder.get_locked("root") is False
    binder.set_locked("soups", False)
    assert binder.get_locked("soups") is False
    binder.add_recipe("soups", "chowder")
    binder.remove_recipe("minestrone")
    assert binder.get_recipes("soups") == ["borscht", "chowder"]


def test_sections_not_in_use_raise_key_error(binder):
    binder.delete_section("mains")
    for name in ["mains", "salads"]:
        with pytest.raises(KeyError):
            binder.set_locked(name, True)
        with pytest.raises(KeyError):
            binder.get_locked(name)


def test_set_locked_changes_no_recipes_or_sections(binder):
    before = [(s, binder.get_recipes(s), binder.get_subsections(s)) for s in ["root", "soups"]]
    binder.set_locked("soups", True)
    binder.set_locked("root", True)
    assert [(s, binder.get_recipes(s), binder.get_subsections(s)) for s in ["root", "soups"]] == before


# --- recipes ----------------------------------------------------------------


def test_add_recipe_into_a_locked_section_changes_nothing(binder):
    binder.set_locked("root", True)
    before = tree(binder)
    with pytest.raises(SectionLocked):
        binder.add_recipe("root", "toast")
    assert tree(binder) == before
    with pytest.raises(KeyError):
        binder.get_section_of("toast")


def test_remove_recipe_from_a_locked_section_changes_nothing(binder):
    binder.set_locked("soups", True)
    before = tree(binder)
    with pytest.raises(SectionLocked):
        binder.remove_recipe("borscht")
    assert tree(binder) == before
    assert binder.get_section_of("borscht") == "soups"


def test_the_sections_below_a_locked_one_are_not_locked(binder):
    binder.set_locked("soups", True)
    binder.add_recipe("cold soups", "salmorejo")
    binder.remove_recipe("gazpacho")
    assert binder.get_recipes("cold soups") == ["salmorejo"]


def test_other_sections_are_not_affected(binder):
    binder.set_locked("soups", True)
    binder.add_recipe("mains", "risotto")
    binder.remove_recipe("lasagne")
    assert binder.get_recipes("mains") == ["risotto"]


# --- deleting ---------------------------------------------------------------


def test_deleting_a_locked_section_changes_nothing(binder):
    binder.set_locked("cold soups", True)
    before = tree(binder)
    with pytest.raises(SectionLocked):
        binder.delete_section("cold soups")
    assert tree(binder) == before


def test_deleting_a_section_whose_parent_is_locked_changes_nothing(binder):
    binder.set_locked("soups", True)
    before = tree(binder)
    with pytest.raises(SectionLocked):
        binder.delete_section("cold soups")
    assert tree(binder) == before
    assert binder.get_section_of("gazpacho") == "cold soups"


def test_deleting_is_allowed_when_only_a_subsection_is_locked(binder):
    binder.set_locked("cold soups", True)
    binder.delete_section("soups")
    assert binder.get_recipes("root") == ["minestrone", "borscht"]
    assert binder.get_subsections("root") == ["mains", "cold soups"]
    assert binder.get_locked("cold soups") is True


def test_deleting_works_again_after_unlocking(binder):
    binder.set_locked("soups", True)
    binder.set_locked("soups", False)
    binder.delete_section("cold soups")
    assert binder.get_recipes("soups") == ["minestrone", "borscht", "gazpacho"]


# --- sections are not affected ----------------------------------------------


def test_sections_can_be_added_to_a_locked_section(binder):
    binder.set_locked("soups", True)
    binder.add_section("hot soups", "soups")
    assert binder.get_subsections("soups") == ["cold soups", "hot soups"]


def test_locked_sections_can_be_moved_and_moved_into(binder):
    binder.set_locked("cold soups", True)
    binder.set_locked("mains", True)
    binder.move_section("cold soups", "mains")
    assert binder.get_subsections("mains") == ["cold soups"]
    assert binder.get_recipes("cold soups") == ["gazpacho"]
    assert binder.get_locked("cold soups") is True
    binder.set_locked("soups", True)
    binder.move_section("cold soups", "soups")
    assert binder.get_subsections("soups") == ["cold soups"]
