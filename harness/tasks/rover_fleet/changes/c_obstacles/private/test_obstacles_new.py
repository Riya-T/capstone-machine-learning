"""Hidden tests for the c_obstacles change (obstacles). Never shown to the
writer or the editor.

Usage (with rovers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_obstacles/private/test_obstacles_new.py
"""

import pytest
from rovers import RoverError, RoverFleet


@pytest.fixture
def fleet():
    f = RoverFleet(width=8, height=6)
    f.land("scout", 2, 2, "north")
    f.add_obstacle(2, 4)
    f.add_obstacle(0, 0)
    return f


def state(f):
    return (
        [(r, f.get_location(r), f.get_odometer(r)) for r in f.get_rovers()],
        f.get_obstacles(),
    )


def test_obstacle_list_keeps_the_order_added(fleet):
    fleet.add_obstacle(7, 5)
    assert fleet.get_obstacles() == [(2, 4), (0, 0), (7, 5)]
    assert RoverFleet().get_obstacles() == []


def test_obstacle_cell_has_no_rover(fleet):
    assert fleet.get_rover_at(2, 4) is None


@pytest.mark.parametrize(
    "cell", [(8, 0), (0, 6), (-1, 2), (2, -1), (1.0, 2), (2, "2"), (None, 0)]
)
def test_obstacle_off_the_plateau_is_rejected(fleet, cell):
    before = state(fleet)
    with pytest.raises(ValueError):
        fleet.add_obstacle(*cell)
    assert state(fleet) == before


def test_obstacle_twice_or_under_a_rover_is_rejected(fleet):
    before = state(fleet)
    with pytest.raises(RoverError):
        fleet.add_obstacle(2, 4)
    with pytest.raises(RoverError):
        fleet.add_obstacle(2, 2)
    assert state(fleet) == before


def test_obstacle_cell_errors_come_before_rover_errors(fleet):
    with pytest.raises(ValueError):
        fleet.add_obstacle(2, 40)
    fleet.drive("scout", "F")  # now at (2, 3)
    fleet.add_obstacle(2, 2)  # the cell it left
    assert fleet.get_obstacles() == [(2, 4), (0, 0), (2, 2)]


def test_obstacle_landing_is_rejected_after_value_errors(fleet):
    before = state(fleet)
    with pytest.raises(RoverError):
        fleet.land("mole", 0, 0, "south")
    with pytest.raises(ValueError):
        fleet.land("mole", 0, 0, "down")
    with pytest.raises(RoverError):
        fleet.land("scout", 0, 0, "down")
    assert state(fleet) == before


def test_obstacle_stops_the_rest_of_the_string(fleet):
    assert fleet.drive("scout", "FFRF") == 1
    assert fleet.get_location("scout") == (2, 3, "north")
    assert fleet.get_odometer("scout") == 1


def test_obstacle_blocks_backward_moves_and_not_turns(fleet):
    fleet.add_obstacle(2, 1)
    assert fleet.drive("scout", "LLRR") == 4
    assert fleet.drive("scout", "B") == 0
    assert fleet.get_location("scout") == (2, 2, "north")


def test_obstacle_across_a_wrapped_edge_blocks(fleet):
    fleet.land("mole", 7, 0, "east")
    assert fleet.drive("mole", "F") == 0
    assert fleet.drive("mole", "LB") == 2  # backward across the south edge
    assert fleet.get_location("mole") == (7, 5, "north")
    fleet.land("digger", 0, 5, "north")
    assert fleet.drive("digger", "F") == 0


def test_obstacle_free_cells_still_open(fleet):
    assert fleet.drive("scout", "RFLFF") == 5
    assert fleet.get_location("scout") == (3, 4, "north")


def test_obstacle_works_with_cliffs():
    f = RoverFleet(width=3, height=3, wrap=False)
    f.land("scout", 0, 1, "east")
    f.add_obstacle(2, 1)
    assert f.drive("scout", "FFLFF") == 1
    assert f.get_location("scout") == (1, 1, "east")
