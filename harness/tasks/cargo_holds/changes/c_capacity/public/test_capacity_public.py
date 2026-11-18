"""Public checks for the c_capacity change (hold capacities). Shown to the
editor, never to the writer.

Usage (with ship.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

import pytest
from ship import HoldFull, Ship


@pytest.fixture
def ship():
    s = Ship()
    s.add_hold("fore", capacity=10)
    s.add_hold("aft")
    return s


def test_a_hold_can_be_filled_up_to_its_capacity(ship):
    ship.load("fore", "grain", 6)
    ship.load("fore", "steel", 4)
    assert ship.get_count("fore", "steel") == 4
    assert ship.get_capacity("fore") == 10
    assert ship.get_capacity("aft") is None


def test_loading_past_the_capacity_raises(ship):
    ship.load("fore", "grain", 8)
    with pytest.raises(HoldFull):
        ship.load("fore", "steel", 3)
    assert ship.get_cargo("fore") == ["grain"]


def test_shift_all_into_a_full_hold_raises(ship):
    ship.load("fore", "grain", 8)
    ship.load("aft", "coal", 5)
    with pytest.raises(HoldFull):
        ship.shift_all("aft", "fore")
    assert ship.get_count("aft", "coal") == 5
