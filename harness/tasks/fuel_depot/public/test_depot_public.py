"""Public checks for depot.py.

Usage (with depot.py importable, e.g. in the sandbox):
    python -m pytest public/test_depot_public.py
"""

import pytest
from depot import Depot, NotEnoughFuel


@pytest.fixture
def depot():
    dep = Depot()
    dep.add_tank("north")
    dep.add_tank("south")
    return dep


def test_fill_then_level(depot):
    depot.fill("north", 500)
    assert depot.get_level("north") == 500
    assert depot.get_level("south") == 0
    with pytest.raises(ValueError):
        depot.fill("north", 0)


def test_draining_more_than_the_level_raises(depot):
    depot.fill("north", 100)
    with pytest.raises(NotEnoughFuel):
        depot.drain("north", 150)
    assert depot.get_level("north") == 100
    assert depot.get_log("north") == [("fill", 100)]


def test_pump_moves_fuel_and_logs_both_tanks(depot):
    depot.fill("north", 300)
    depot.pump("north", "south", 120)
    assert depot.get_level("north") == 180
    assert depot.get_level("south") == 120
    assert depot.get_log("north") == [("fill", 300), ("out", 120)]
    assert depot.get_log("south") == [("in", 120)]


def test_pump_down_moves_what_is_above_keep(depot):
    depot.fill("north", 300)
    assert depot.pump_down("north", "south", 100) == 200
    assert depot.get_level("north") == 100
    assert depot.get_level("south") == 200
    # Nothing is above keep any more: nothing moves and nothing is logged.
    assert depot.pump_down("north", "south", 100) == 0
    assert depot.get_log("north") == [("fill", 300), ("out", 200)]
    assert depot.get_log("south") == [("in", 200)]
    # keep may be 0: then everything moves.
    assert depot.pump_down("south", "north", 0) == 200
    assert depot.get_level("north") == 300


def test_retire_tank_moves_everything_and_retires_the_tank(depot):
    depot.fill("north", 70)
    assert depot.retire_tank("north", "south") == 70
    assert depot.get_level("south") == 70
    assert depot.get_log("south") == [("in", 70)]
    assert depot.get_tanks() == ["south"]
    with pytest.raises(KeyError):
        depot.get_level("north")
    # The id may be added again, as a new empty tank.
    depot.add_tank("north")
    assert depot.get_tanks() == ["south", "north"]
    assert depot.get_level("north") == 0
    assert depot.get_log("north") == []


def test_an_empty_tank_is_retired_without_logging_anything(depot):
    depot.fill("south", 10)
    assert depot.retire_tank("north", "south") == 0
    assert depot.get_tanks() == ["south"]
    assert depot.get_level("south") == 10
    assert depot.get_log("south") == [("fill", 10)]
