"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with binder.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from binder import BinderError, RecipeBinder


@pytest.fixture
def binder():
    b = RecipeBinder()
    b.add_section("soups", "root")
    b.add_section("desserts", "root")
    return b


def test_undo_takes_back_the_last_recipe(binder):
    binder.add_recipe("soups", "minestrone")
    binder.add_recipe("soups", "borscht")
    binder.undo()
    assert binder.get_recipes("soups") == ["minestrone"]
    binder.undo()
    assert binder.get_recipes("soups") == []


def test_undo_takes_back_a_move(binder):
    binder.move_section("soups", "desserts")
    binder.undo()
    assert binder.get_subsections("root") == ["soups", "desserts"]
    assert binder.get_subsections("desserts") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(BinderError):
        RecipeBinder().undo()
