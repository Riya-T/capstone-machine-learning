"""Public checks for ship.py.

Usage (with ship.py importable, e.g. in the sandbox):
    python -m pytest public/test_ship_public.py
"""

import pytest
from ship import NotEnoughCrates, Ship


@pytest.fixture
def ship():
    s = Ship()
    s.add_hold("fore")
    s.add_hold("aft")
    return s


def test_loading_and_unloading_change_the_count(ship):
    ship.load("fore", "grain", 5)
    ship.load("fore", "grain", 2)
    ship.unload("fore", "grain", 3)
    assert ship.get_count("fore", "grain") == 4
    assert ship.get_count("fore", "steel") == 0


def test_unloading_more_than_there_are_raises(ship):
    ship.load("fore", "grain", 5)
    with pytest.raises(NotEnoughCrates):
        ship.unload("fore", "grain", 6)
    assert ship.get_count("fore", "grain") == 5


def test_cargo_is_listed_alphabetically_and_only_while_there_are_crates(ship):
    ship.load("fore", "steel", 2)
    ship.load("fore", "coal", 1)
    ship.load("fore", "grain", 4)
    ship.unload("fore", "coal", 1)
    assert ship.get_cargo("fore") == ["grain", "steel"]


def test_shift_all_moves_every_cargo_type_and_returns_how_many(ship):
    ship.load("fore", "grain", 5)
    ship.load("fore", "steel", 2)
    ship.load("aft", "coal", 1)
    assert ship.shift_all("fore", "aft") == 7
    assert ship.get_cargo("fore") == []
    assert ship.get_cargo("aft") == ["coal", "grain", "steel"]
    assert ship.get_holds() == ["fore", "aft"]


def test_a_sealed_hold_is_gone(ship):
    ship.load("fore", "grain", 5)
    ship.load("aft", "grain", 1)
    assert ship.seal_hold("fore", "aft") == 5
    assert ship.get_holds() == ["aft"]
    assert ship.get_count("aft", "grain") == 6
    with pytest.raises(KeyError):
        ship.get_count("fore", "grain")
    with pytest.raises(KeyError):
        ship.load("fore", "grain", 1)
