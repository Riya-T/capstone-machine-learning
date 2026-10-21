"""Public checks for the c_expired change (the current day and expired
batches). Shown to the editor, never to the writer.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_expired/public/test_expired_public.py
"""

import pytest
from pantry import Pantry, PantryError


@pytest.fixture
def pantry():
    pan = Pantry()
    pan.add_item("milk", 2, 3)
    pan.add_item("milk", 5, 8)
    pan.add_item("rice", 10, 30)
    return pan


def test_moving_the_day_on_expires_earlier_batches(pantry):
    assert pantry.get_day() == 0
    pantry.set_day(5)
    assert pantry.get_day() == 5
    assert pantry.get_usable_quantity("milk") == 5
    assert pantry.get_expired_quantity("milk") == 2
    assert pantry.get_quantity("milk") == 7


def test_expired_batches_cannot_be_used(pantry):
    pantry.set_day(5)
    with pytest.raises(PantryError):
        pantry.use_item("milk", 6)
    pantry.use_item("milk", 5)
    assert pantry.get_batches("milk") == [(3, 2)]


def test_discarding_removes_expired_batches(pantry):
    pantry.set_day(5)
    assert pantry.discard_expired("milk") == 2
    assert pantry.get_batches("milk") == [(8, 5)]
    assert pantry.discard_expired("rice") == 0
