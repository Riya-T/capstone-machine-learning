"""Public checks for the c_queries change (query). Shown to the editor, never
to the writer.

Usage (with binder.py importable, e.g. in the sandbox):
    python -m pytest changes/c_queries/public/test_queries_public.py
"""

from binder import RecipeBinder


def make():
    b = RecipeBinder()
    b.add_section("soups", "root")
    b.add_section("cold soups", "soups")
    b.add_recipe("soups", "minestrone")
    b.add_recipe("cold soups", "gazpacho")
    b.add_recipe("root", "toast")
    return b


def test_all_recipes_lists_a_section_before_its_subsections():
    b = make()
    assert b.get_all_recipes("root") == ["toast", "minestrone", "gazpacho"]
    assert b.get_all_recipes("cold soups") == ["gazpacho"]


def test_path_goes_from_root_down_to_the_section():
    b = make()
    assert b.get_path("cold soups") == ["root", "soups", "cold soups"]
    assert b.get_path("root") == ["root"]
