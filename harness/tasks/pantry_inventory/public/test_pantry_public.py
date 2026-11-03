"""Public checks for pantry.py.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest public/test_pantry_public.py
"""

import pytest
from pantry import Pantry


@pytest.fixture
def pantry():
    pan = Pantry()
    pan.add_item("rice", 10, 30)
    pan.add_item("milk", 2, 3)
    return pan


def left(pan, name):
    """The item's batches that still have units. Whether a used-up batch is
    still listed, as (use_by, 0), is up to the program, so those are skipped."""
    return [batch for batch in pan.get_batches(name) if batch[1] != 0]


def test_adding_then_quantity(pantry):
    assert pantry.get_quantity("milk") == 2
    pantry.add_item("milk", 4, 8)
    assert pantry.get_quantity("milk") == 6
    assert pantry.get_batches("milk") == [(3, 2), (8, 4)]
    assert pantry.get_items() == ["rice", "milk"]


def test_using_takes_from_the_batch_added_first(pantry):
    pantry.add_item("milk", 4, 8)
    pantry.add_item("milk", 1, 1)
    pantry.use_item("milk", 4)
    assert left(pantry, "milk") == [(8, 2), (1, 1)]
    assert pantry.get_quantity("milk") == 3
    pantry.use_item("milk", 2)
    assert left(pantry, "milk") == [(1, 1)]


def test_using_more_than_there_is_takes_what_is_left(pantry):
    pantry.add_item("milk", 1, 5)
    pantry.use_item("milk", 5)
    assert pantry.get_quantity("milk") == 0
    assert left(pantry, "milk") == []
    assert pantry.get_items() == ["rice", "milk"]


def test_expiring_by_adds_up_the_units_left_that_are_due(pantry):
    pantry.add_item("beans", 5, 2)
    pantry.add_item("milk", 3, 5)
    assert pantry.get_expiring_by(6) == [("milk", 5), ("beans", 5)]
    assert pantry.get_expiring_by(1) == []
    pantry.use_item("milk", 2)  # the day-3 batch is used up
    assert pantry.get_expiring_by(4) == [("beans", 5)]


def test_quantities_must_be_positive(pantry):
    with pytest.raises(ValueError):
        pantry.add_item("milk", 0, 3)
    with pytest.raises(ValueError):
        pantry.use_item("milk", -1)


def test_unknown_item_raises_key_error(pantry):
    with pytest.raises(KeyError):
        pantry.get_quantity("eggs")
