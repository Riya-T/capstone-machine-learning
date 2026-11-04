"""Public checks for the c_categories change (item categories). Shown to
the editor, never to the writer.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_categories/public/test_categories_public.py
"""

from pantry import Pantry


def test_items_are_grouped_by_category():
    pan = Pantry()
    pan.add_item("milk", 2, 3, category="dairy")
    pan.add_item("rice", 10, 30)
    pan.add_item("cheese", 1, 9, category="dairy")
    assert pan.get_category("milk") == "dairy"
    assert pan.get_category("rice") == "other"
    assert pan.get_items_in("dairy") == ["milk", "cheese"]
    assert pan.get_categories() == ["dairy", "other"]
    assert pan.get_category_quantity("dairy") == 3


def test_an_item_can_be_moved_to_another_category():
    pan = Pantry()
    pan.add_item("rice", 10, 30)
    pan.set_category("rice", "grains")
    assert pan.get_category("rice") == "grains"
    assert pan.get_items_in("other") == []
    assert pan.get_categories() == ["grains"]


def test_adding_to_an_existing_item_keeps_or_replaces_its_category():
    pan = Pantry()
    pan.add_item("milk", 2, 3, category="dairy")
    pan.add_item("milk", 4, 8)
    assert pan.get_category("milk") == "dairy"
    assert pan.get_quantity("milk") == 6
    pan.add_item("milk", 1, 9, category="drinks")
    assert pan.get_category("milk") == "drinks"
    assert pan.get_items_in("dairy") == []
    assert pan.get_category_quantity("drinks") == 7


def test_categories_follow_the_first_item_in_each():
    pan = Pantry()
    pan.add_item("milk", 2, 3, category="dairy")
    pan.add_item("rice", 10, 30)
    pan.add_item("cheese", 1, 9, category="dairy")
    pan.set_category("rice", "grains")
    pan.set_category("milk", "drinks")
    assert pan.get_categories() == ["drinks", "grains", "dairy"]
