"""Public checks for the c_expired change (the current day and expired
batches). Shown to the editor, never to the writer.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_expired/public/test_expired_public.py
"""

import pytest
from pantry import Pantry


@pytest.fixture
def pantry():
    pan = Pantry()
    pan.add_item("milk", 2, 3)
    pan.add_item("milk", 5, 8)
    pan.add_item("rice", 10, 30)
    return pan


def usable(pan, name):
    """The item's batches that are not expired and still have units
    (whether a used-up batch is still listed, as (use_by, 0), is up to the
    program)."""
    return [b for b in pan.get_batches(name) if b[0] >= pan.get_day() and b[1] != 0]


def expired(pan, name):
    """The item's expired batches that are still listed."""
    return [b for b in pan.get_batches(name) if b[0] < pan.get_day() and b[1] != 0]


def test_moving_the_day_on_expires_earlier_batches(pantry):
    assert pantry.get_day() == 0
    pantry.set_day(3)  # the day-3 batch is still usable on day 3
    assert pantry.get_usable_quantity("milk") == 7
    assert pantry.get_expired_quantity("milk") == 0
    pantry.set_day(5)
    assert pantry.get_day() == 5
    assert pantry.get_usable_quantity("milk") == 5
    assert pantry.get_expired_quantity("milk") == 2
    assert pantry.get_quantity("milk") == 7


def test_expired_batches_cannot_be_used(pantry):
    pantry.set_day(5)
    pantry.use_item("milk", 4)
    assert usable(pantry, "milk") == [(8, 1)]
    pantry.use_item("milk", 6)  # only 1 usable unit is left
    assert usable(pantry, "milk") == []
    assert pantry.get_usable_quantity("milk") == 0
    # the day-3 batch is still listed with all its units, or thrown away
    assert expired(pantry, "milk") in ([(3, 2)], [])
    assert pantry.get_quantity("milk") == pantry.get_expired_quantity("milk")


def test_an_expired_batch_between_usable_ones_is_skipped():
    pan = Pantry()
    pan.add_item("milk", 4, 8)
    pan.add_item("milk", 2, 3)
    pan.add_item("milk", 3, 6)
    pan.set_day(4)
    pan.use_item("milk", 5)
    assert usable(pan, "milk") == [(6, 2)]
    assert pan.get_usable_quantity("milk") == 2


def test_discarding_removes_expired_batches(pantry):
    pantry.set_day(5)
    assert pantry.discard_expired("milk") == 2
    assert pantry.get_batches("milk") == [(8, 5)]
    assert pantry.discard_expired("rice") == 0
