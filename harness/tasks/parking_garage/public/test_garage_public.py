"""Public checks for garage.py.

Usage (with garage.py importable, e.g. in the sandbox):
    python -m pytest public/test_garage_public.py
"""

import pytest
from garage import Garage, GarageFull


@pytest.fixture
def garage():
    gar = Garage()
    gar.add_level("P1", 2)
    gar.add_level("P2", 1)
    return gar


def test_vehicles_fill_the_first_level_before_the_next(garage):
    assert garage.enter("AAA", 10) == "P1"
    assert garage.enter("BBB", 12) == "P1"
    assert garage.enter("CCC", 15) == "P2"
    assert garage.get_vehicles("P1") == ["AAA", "BBB"]
    assert garage.get_free_spots("P1") == 0
    assert garage.get_level("CCC") == "P2"


def test_leaving_returns_the_minutes_parked_and_frees_the_spot(garage):
    garage.enter("AAA", 100)
    assert garage.leave("AAA", 145) == 45
    assert garage.get_free_spots("P1") == 2
    assert garage.get_vehicles("P1") == []


def test_a_full_garage_raises(garage):
    for plate, minute in [("AAA", 1), ("BBB", 2), ("CCC", 3)]:
        garage.enter(plate, minute)
    with pytest.raises(GarageFull):
        garage.enter("DDD", 4)
    assert garage.get_free_spots("P2") == 0


def test_unknown_levels_and_plates_raise_key_error(garage):
    with pytest.raises(KeyError):
        garage.get_free_spots("P9")
    with pytest.raises(KeyError):
        garage.get_level("ZZZ")


def test_spot_counts_must_be_positive():
    gar = Garage()
    with pytest.raises(ValueError):
        gar.add_level("P1", 0)
    assert gar.get_levels() == []
