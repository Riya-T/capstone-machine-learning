"""Public checks for rovers.py.

Usage (with rovers.py importable, e.g. in the sandbox):
    python -m pytest public/test_rovers_public.py
"""

import pytest
from rovers import RoverFleet


@pytest.fixture
def fleet():
    f = RoverFleet()
    f.land("scout", 2, 2, "north")
    return f


def test_landing_and_location(fleet):
    fleet.land("digger", 5, 7, "west")
    assert fleet.get_rovers() == ["scout", "digger"]
    assert fleet.get_location("digger") == (5, 7, "west")
    assert fleet.get_rover_at(5, 7) == "digger"
    assert fleet.get_rover_at(0, 0) is None


def test_moving_and_turning(fleet):
    assert fleet.drive("scout", "FFRFB") == 5
    assert fleet.get_location("scout") == (2, 4, "east")
    fleet.drive("scout", "LL")
    assert fleet.get_location("scout") == (2, 4, "west")


def test_driving_off_the_east_edge_comes_back_in_the_west():
    f = RoverFleet()
    f.land("scout", 9, 3, "east")
    f.drive("scout", "F")
    assert f.get_location("scout") == (0, 3, "east")


def test_a_rover_in_the_way_blocks_the_move(fleet):
    fleet.land("digger", 2, 4, "south")
    assert fleet.drive("scout", "RLFF") == 3
    assert fleet.get_location("scout") == (2, 3, "north")
    assert fleet.get_location("digger") == (2, 4, "south")


def test_odometer_counts_cells(fleet):
    fleet.drive("scout", "FFB")
    assert fleet.get_odometer("scout") == 3


def test_invalid_commands_change_nothing(fleet):
    with pytest.raises(ValueError):
        fleet.drive("scout", "FFx")
    assert fleet.get_location("scout") == (2, 2, "north")
    assert fleet.get_odometer("scout") == 0
