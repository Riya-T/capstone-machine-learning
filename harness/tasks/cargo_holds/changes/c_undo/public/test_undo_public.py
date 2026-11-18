"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with ship.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from ship import CargoError, Ship


@pytest.fixture
def ship():
    s = Ship()
    s.add_hold("fore")
    s.add_hold("aft")
    return s


def test_undo_takes_back_the_last_load(ship):
    ship.load("fore", "grain", 5)
    ship.load("fore", "grain", 2)
    ship.undo()
    assert ship.get_count("fore", "grain") == 5
    ship.undo()
    assert ship.get_cargo("fore") == []


def test_undo_takes_back_a_shift(ship):
    ship.load("fore", "grain", 4)
    assert ship.shift_all("fore", "aft") == 4
    ship.undo()
    assert ship.get_count("fore", "grain") == 4
    assert ship.get_count("aft", "grain") == 0


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(CargoError):
        Ship().undo()
