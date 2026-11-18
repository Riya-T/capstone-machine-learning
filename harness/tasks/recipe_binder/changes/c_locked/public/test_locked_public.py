"""Public checks for the c_locked change (state flag). Shown to the editor,
never to the writer.

Usage (with binder.py importable, e.g. in the sandbox):
    python -m pytest changes/c_locked/public/test_locked_public.py
"""

import pytest
from binder import RecipeBinder, SectionLocked


@pytest.fixture
def binder():
    b = RecipeBinder()
    b.add_section("soups", "root")
    b.add_recipe("soups", "minestrone")
    return b


def test_sections_start_unlocked(binder):
    assert binder.get_locked("soups") is False
    binder.set_locked("soups", True)
    assert binder.get_locked("soups") is True


def test_a_locked_section_takes_no_new_recipes(binder):
    binder.set_locked("soups", True)
    with pytest.raises(SectionLocked):
        binder.add_recipe("soups", "borscht")
    assert binder.get_recipes("soups") == ["minestrone"]


def test_a_locked_section_cannot_be_deleted(binder):
    binder.set_locked("soups", True)
    with pytest.raises(SectionLocked):
        binder.delete_section("soups")
    assert binder.get_subsections("root") == ["soups"]
