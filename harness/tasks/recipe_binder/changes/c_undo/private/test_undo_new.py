"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with binder.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
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
    b.add_section("fish", "soups")
    b.add_recipe("soups", "minestrone")
    b.add_recipe("soups", "borscht")
    b.add_recipe("soups", "chowder")
    b.add_recipe("cold soups", "gazpacho")
    b.add_recipe("mains", "lasagne")
    return b


def tree(b, section="root"):
    return (section, b.get_recipes(section), [tree(b, s) for s in b.get_subsections(section)])


def where(b, section="root"):
    found = {r: b.get_section_of(r) for r in b.get_recipes(section)}
    for s in b.get_subsections(section):
        found.update(where(b, s))
    return found


# --- each call can be undone ------------------------------------------------


def test_undo_of_add_recipe_frees_the_name(binder):
    before = tree(binder)
    binder.add_recipe("desserts", "flan")
    binder.undo()
    assert tree(binder) == before
    with pytest.raises(KeyError):
        binder.get_section_of("flan")
    binder.add_recipe("mains", "flan")
    assert binder.get_recipes("mains") == ["lasagne", "flan"]


def test_undo_of_remove_recipe_puts_it_back_in_its_place(binder):
    before = tree(binder)
    binder.remove_recipe("borscht")
    binder.undo()
    assert tree(binder) == before
    assert binder.get_recipes("soups") == ["minestrone", "borscht", "chowder"]
    assert binder.get_section_of("borscht") == "soups"
    with pytest.raises(BinderError):
        binder.add_recipe("mains", "borscht")


def test_undo_of_move_section_puts_it_back_in_its_place(binder):
    before = tree(binder)
    binder.move_section("cold soups", "mains")
    binder.undo()
    assert tree(binder) == before
    assert binder.get_subsections("soups") == ["cold soups", "fish"]
    assert binder.get_subsections("mains") == []


def test_undo_of_moving_a_whole_branch(binder):
    before, before_where = tree(binder), where(binder)
    binder.move_section("soups", "desserts")
    binder.undo()
    assert tree(binder) == before
    assert where(binder) == before_where
    assert binder.get_subsections("root") == ["soups", "mains", "desserts"]


def test_undo_of_delete_section_brings_it_back_with_its_contents(binder):
    before, before_where = tree(binder), where(binder)
    binder.delete_section("soups")
    assert binder.get_recipes("root") == ["minestrone", "borscht", "chowder"]
    binder.undo()
    assert tree(binder) == before
    assert where(binder) == before_where
    assert binder.get_recipes("root") == []
    assert binder.get_subsections("root") == ["soups", "mains", "desserts"]


def test_undo_of_delete_section_keeps_its_place_among_its_siblings(binder):
    binder.add_section("salads", "mains")
    binder.add_recipe("desserts", "flan")
    before = tree(binder)
    binder.delete_section("mains")
    assert binder.get_subsections("root") == ["soups", "desserts", "salads"]
    binder.undo()
    assert binder.get_subsections("root") == ["soups", "mains", "desserts"]
    assert binder.get_subsections("mains") == ["salads"]
    assert tree(binder) == before


def test_undo_of_delete_section_when_the_parent_had_recipes(binder):
    binder.add_recipe("cold soups", "salmorejo")
    before = tree(binder)
    binder.delete_section("cold soups")
    assert binder.get_recipes("soups") == ["minestrone", "borscht", "chowder", "gazpacho", "salmorejo"]
    binder.undo()
    assert tree(binder) == before
    assert binder.get_section_of("salmorejo") == "cold soups"


def test_a_section_brought_back_is_in_use_again(binder):
    binder.delete_section("cold soups")
    binder.undo()
    binder.add_recipe("cold soups", "salmorejo")
    assert binder.get_recipes("cold soups") == ["gazpacho", "salmorejo"]
    with pytest.raises(BinderError):
        binder.add_section("cold soups", "root")
    binder.move_section("cold soups", "desserts")
    assert binder.get_subsections("desserts") == ["cold soups"]


def test_undo_of_add_section_removes_it_and_frees_the_name(binder):
    binder.add_section("salads", "mains")
    binder.undo()
    assert binder.get_subsections("mains") == []
    with pytest.raises(KeyError):
        binder.get_recipes("salads")
    binder.add_section("salads", "desserts")
    assert binder.get_subsections("desserts") == ["salads"]


def test_undo_of_deleting_an_empty_section(binder):
    binder.delete_section("desserts")
    binder.undo()
    assert binder.get_subsections("root") == ["soups", "mains", "desserts"]
    binder.undo()  # the arrival of lasagne
    assert binder.get_recipes("mains") == []


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    b = RecipeBinder()
    calls = [
        lambda: b.add_section("soups", "root"),
        lambda: b.add_section("mains", "root"),
        lambda: b.add_recipe("soups", "minestrone"),
        lambda: b.add_section("cold soups", "soups"),
        lambda: b.add_recipe("cold soups", "gazpacho"),
        lambda: b.add_recipe("soups", "borscht"),
        lambda: b.add_recipe("mains", "lasagne"),
        lambda: b.move_section("cold soups", "mains"),
        lambda: b.remove_recipe("minestrone"),
        lambda: b.add_section("fish", "cold soups"),
        lambda: b.add_recipe("fish", "paella"),
        lambda: b.delete_section("cold soups"),
        lambda: b.move_section("mains", "soups"),
        lambda: b.delete_section("soups"),
        lambda: b.remove_recipe("lasagne"),
    ]
    states = [(tree(b), where(b))]
    for call in calls:
        call()
        states.append((tree(b), where(b)))
    assert b.get_recipes("root") == ["borscht"]
    assert b.get_subsections("root") == ["mains"]
    assert b.get_recipes("mains") == ["gazpacho"]
    assert b.get_subsections("mains") == ["fish"]
    for expected in reversed(states[:-1]):
        b.undo()
        assert (tree(b), where(b)) == expected
    with pytest.raises(BinderError):
        b.undo()
    assert tree(b) == ("root", [], [])


def test_failed_calls_are_not_recorded(binder):
    binder.add_recipe("desserts", "flan")
    for call in (
        lambda: binder.add_section("soups", "root"),
        lambda: binder.add_section("salads", "nowhere"),
        lambda: binder.add_recipe("mains", "gazpacho"),
        lambda: binder.add_recipe("nowhere", "stew"),
        lambda: binder.remove_recipe("risotto"),
        lambda: binder.move_section("soups", "cold soups"),
        lambda: binder.move_section("root", "mains"),
        lambda: binder.delete_section("root"),
        lambda: binder.delete_section("nowhere"),
    ):
        with pytest.raises((KeyError, BinderError)):
            call()
    binder.undo()  # the arrival of flan
    assert binder.get_recipes("desserts") == []
    assert binder.get_recipes("mains") == ["lasagne"]


def test_get_calls_are_not_recorded(binder):
    binder.add_recipe("desserts", "flan")
    binder.get_recipes("desserts")
    binder.get_subsections("root")
    binder.get_section_of("flan")
    binder.undo()
    assert binder.get_recipes("desserts") == []
    assert binder.get_recipes("mains") == ["lasagne"]


def test_there_is_no_redo():
    b = RecipeBinder()
    b.add_section("soups", "root")
    b.add_recipe("soups", "minestrone")
    b.undo()
    b.undo()
    assert b.get_subsections("root") == []
    with pytest.raises(BinderError):
        b.undo()


def test_new_calls_after_an_undo_are_undone_first(binder):
    binder.remove_recipe("minestrone")
    binder.undo()
    binder.move_section("fish", "mains")
    binder.undo()
    assert binder.get_subsections("soups") == ["cold soups", "fish"]
    assert binder.get_recipes("soups") == ["minestrone", "borscht", "chowder"]
    binder.undo()  # the arrival of lasagne in the fixture
    assert binder.get_recipes("mains") == []


def test_nothing_left_to_undo_raises_and_changes_nothing():
    b = RecipeBinder()
    with pytest.raises(BinderError):
        b.undo()
    b.add_section("soups", "root")
    b.undo()
    with pytest.raises(BinderError):
        b.undo()
    assert b.get_subsections("root") == []
    b.add_section("soups", "root")
    b.add_recipe("soups", "minestrone")
    assert b.get_recipes("soups") == ["minestrone"]


def test_the_whole_fixture_can_be_undone(binder):
    for _ in range(10):
        binder.undo()
    assert tree(binder) == ("root", [], [])
    with pytest.raises(BinderError):
        binder.undo()


def test_undo_restores_what_a_later_call_checks(binder):
    binder.move_section("soups", "desserts")
    binder.undo()
    # fish is still below soups, and soups is no longer below desserts.
    with pytest.raises(BinderError):
        binder.move_section("soups", "fish")
    binder.move_section("desserts", "fish")
    assert binder.get_subsections("fish") == ["desserts"]
    binder.delete_section("mains")
    binder.undo()
    with pytest.raises(BinderError):
        binder.add_recipe("root", "lasagne")
