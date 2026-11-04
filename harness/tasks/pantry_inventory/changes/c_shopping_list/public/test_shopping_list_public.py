"""Public checks for the c_shopping_list change (minimum stock and a
shopping list). Shown to the editor, never to the writer.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_shopping_list/public/test_shopping_list_public.py
"""

import pytest
from pantry import Pantry


def test_items_below_their_minimum_are_on_the_list():
    pan = Pantry()
    pan.add_item("milk", 2, 3)
    pan.add_item("rice", 10, 30)
    pan.set_minimum("milk", 6)
    pan.set_minimum("rice", 10)
    assert pan.get_minimum("milk") == 6
    assert pan.get_shopping_list() == [("milk", 4)]


def test_a_day_leaves_out_batches_past_their_use_by_day():
    pan = Pantry()
    pan.add_item("milk", 2, 3)
    pan.add_item("milk", 4, 8)
    pan.set_minimum("milk", 5)
    assert pan.get_shopping_list() == []
    assert pan.get_shopping_list(day=5) == [("milk", 1)]


def test_a_day_that_is_not_an_int_of_0_or_more_is_rejected():
    pan = Pantry()
    pan.add_item("milk", 2, 3)
    with pytest.raises(ValueError):
        pan.get_shopping_list(day=-1)
    with pytest.raises(ValueError):
        pan.get_shopping_list(day="3")
