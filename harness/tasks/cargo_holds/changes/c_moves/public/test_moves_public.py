"""Public checks for the c_moves change (restowing plans). Shown to the
editor, never to the writer.

Usage (with ship.py importable, e.g. in the sandbox):
    python -m pytest changes/c_moves/public/test_moves_public.py
"""

import pytest
from ship import NotEnoughCrates, Ship


@pytest.fixture
def ship():
    s = Ship()
    s.add_hold("fore")
    s.add_hold("aft")
    s.load("fore", "grain", 5)
    s.load("fore", "steel", 2)
    return s


def test_apply_moves_carries_out_every_move(ship):
    assert ship.apply_moves([("grain", "fore", "aft", 3), ("steel", "fore", "aft", 2)]) == 5
    assert ship.get_count("fore", "grain") == 2
    assert ship.get_count("aft", "grain") == 3
    assert ship.get_cargo("fore") == ["grain"]


def test_a_plan_with_a_bad_move_changes_nothing(ship):
    with pytest.raises(NotEnoughCrates):
        ship.apply_moves([("grain", "fore", "aft", 3), ("steel", "fore", "aft", 9)])
    assert ship.get_count("fore", "grain") == 5
    assert ship.get_cargo("aft") == []
