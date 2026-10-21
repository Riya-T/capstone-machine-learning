"""Public checks for pantry.py.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest public/test_pantry_public.py
"""

import pytest
from pantry import Pantry, PantryError


@pytest.fixture
def pantry():
    pan = Pantry()
    pan.add_item("rice", 10, 30)
    pan.add_item("milk", 2, 3)
    return pan


def test_adding_then_quantity(pantry):
    assert pantry.get_quantity("milk") == 2
    pantry.add_item("milk", 4, 8)
    assert pantry.get_quantity("milk") == 6
    assert pantry.get_items() == ["rice", "milk"]


def test_using_takes_from_the_earliest_batch_first(pantry):
    pantry.add_item("milk", 4, 8)
    pantry.use_item("milk", 3)
    assert pantry.get_batches("milk") == [(8, 3)]
    assert pantry.get_quantity("milk") == 3


def test_using_more_than_there_is_raises(pantry):
    with pytest.raises(PantryError):
        pantry.use_item("milk", 3)
    assert pantry.get_quantity("milk") == 2


def test_expiring_by_lists_items_in_the_order_added(pantry):
    pantry.add_item("beans", 5, 4)
    assert pantry.get_expiring_by(6) == ["milk", "beans"]
    assert pantry.get_expiring_by(1) == []


def test_quantities_must_be_positive(pantry):
    with pytest.raises(ValueError):
        pantry.add_item("milk", 0, 3)
    with pytest.raises(ValueError):
        pantry.use_item("milk", -1)


def test_unknown_item_raises_key_error(pantry):
    with pytest.raises(KeyError):
        pantry.get_quantity("eggs")
