"""Hidden tests for the initial rover_fleet spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with rovers.py importable, e.g. in the sandbox):
    python -m pytest private/test_rovers_initial.py
"""

import pytest
from rovers import RoverError, RoverFleet

BAD_COORDINATES = [-1, 10, 1.0, "3", None]
BAD_COMMANDS = ["FFx", "f", "F F", "FB1", None, 3, ["F"]]


@pytest.fixture
def fleet():
    f = RoverFleet()
    f.land("scout", 2, 2, "north")
    f.land("digger", 7, 5, "east")
    return f


def state(f):
    """Every rover's location and odometer, to check that a failed call
    changed nothing."""
    return [(r, f.get_location(r), f.get_odometer(r)) for r in f.get_rovers()]


# --- landing ----------------------------------------------------------------


def test_rovers_are_listed_in_landing_order():
    f = RoverFleet()
    for i, name in enumerate(["mole", "scout", "digger"]):
        f.land(name, i, 0, "south")
    assert f.get_rovers() == ["mole", "scout", "digger"]


def test_a_new_rover_has_its_location_and_no_distance(fleet):
    assert fleet.get_location("digger") == (7, 5, "east")
    assert fleet.get_odometer("digger") == 0


@pytest.mark.parametrize("corner", [(0, 0), (9, 9), (0, 9), (9, 0)])
def test_rovers_can_land_on_the_corners(corner):
    f = RoverFleet()
    f.land("scout", *corner, "west")
    assert f.get_rover_at(*corner) == "scout"


def test_an_empty_rover_id_is_rejected(fleet):
    before = state(fleet)
    with pytest.raises(ValueError):
        fleet.land("", 0, 0, "north")
    assert state(fleet) == before


def test_a_rover_id_in_use_is_rejected(fleet):
    before = state(fleet)
    with pytest.raises(RoverError):
        fleet.land("scout", 0, 0, "north")
    assert state(fleet) == before


@pytest.mark.parametrize("value", BAD_COORDINATES)
def test_invalid_landing_cells_are_rejected(fleet, value):
    before = state(fleet)
    with pytest.raises(ValueError):
        fleet.land("mole", value, 0, "north")
    with pytest.raises(ValueError):
        fleet.land("mole", 0, value, "north")
    assert state(fleet) == before


@pytest.mark.parametrize("facing", ["N", "North", "up", "", None])
def test_invalid_facings_are_rejected(fleet, facing):
    before = state(fleet)
    with pytest.raises(ValueError):
        fleet.land("mole", 0, 0, facing)
    assert state(fleet) == before


def test_landing_on_a_rover_is_rejected(fleet):
    before = state(fleet)
    with pytest.raises(RoverError):
        fleet.land("mole", 7, 5, "north")
    assert state(fleet) == before


def test_landing_errors_come_in_order(fleet):
    with pytest.raises(ValueError):
        fleet.land("", 7, 5, "up")
    with pytest.raises(RoverError):
        fleet.land("scout", -1, 0, "up")
    with pytest.raises(ValueError):
        fleet.land("mole", 7, 5, "up")
    with pytest.raises(ValueError):
        fleet.land("mole", 7, 50, "north")
    assert fleet.get_rovers() == ["scout", "digger"]


# --- lookups ----------------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.drive("mole", "F"),
        lambda f: f.drive("mole", "bad"),
        lambda f: f.get_location("mole"),
        lambda f: f.get_odometer("mole"),
        lambda f: f.get_location(None),
        lambda f: f.drive(1, "F"),
    ],
)
def test_unknown_rovers_raise_key_error(fleet, call):
    before = state(fleet)
    with pytest.raises(KeyError):
        call(fleet)
    assert state(fleet) == before


def test_get_rover_at_finds_rovers(fleet):
    assert fleet.get_rover_at(2, 2) == "scout"
    assert fleet.get_rover_at(7, 5) == "digger"
    assert fleet.get_rover_at(5, 7) is None


@pytest.mark.parametrize("value", BAD_COORDINATES)
def test_get_rover_at_rejects_cells_off_the_plateau(fleet, value):
    with pytest.raises(ValueError):
        fleet.get_rover_at(value, 2)
    with pytest.raises(ValueError):
        fleet.get_rover_at(2, value)


# --- driving ----------------------------------------------------------------


@pytest.mark.parametrize(
    "facing, forward",
    [("north", (2, 3)), ("east", (3, 2)), ("south", (2, 1)), ("west", (1, 2))],
)
def test_forward_and_backward_in_every_direction(facing, forward):
    f = RoverFleet()
    f.land("scout", 2, 2, facing)
    f.drive("scout", "F")
    assert f.get_location("scout") == (*forward, facing)
    f.drive("scout", "BB")
    back = (4 - forward[0], 4 - forward[1])
    assert f.get_location("scout") == (*back, facing)


def test_turning_all_the_way_round(fleet):
    seen = []
    for _ in range(4):
        fleet.drive("scout", "R")
        seen.append(fleet.get_location("scout")[2])
    assert seen == ["east", "south", "west", "north"]
    seen = []
    for _ in range(4):
        fleet.drive("scout", "L")
        seen.append(fleet.get_location("scout")[2])
    assert seen == ["west", "south", "east", "north"]


@pytest.mark.parametrize(
    "start, commands, end",
    [
        ((9, 4, "east"), "F", (0, 4, "east")),
        ((0, 4, "west"), "F", (9, 4, "west")),
        ((4, 9, "north"), "F", (4, 0, "north")),
        ((4, 0, "south"), "F", (4, 9, "south")),
        ((0, 0, "north"), "B", (0, 9, "north")),
        ((0, 0, "east"), "B", (9, 0, "east")),
    ],
)
def test_the_plateau_wraps_at_every_edge(start, commands, end):
    f = RoverFleet()
    f.land("scout", *start)
    f.drive("scout", commands)
    assert f.get_location("scout") == end
    assert f.get_odometer("scout") == 1


def test_a_long_drive_wraps_more_than_once():
    f = RoverFleet()
    f.land("scout", 3, 3, "north")
    assert f.drive("scout", "F" * 25) == 25
    assert f.get_location("scout") == (3, 8, "north")


def test_drive_returns_the_number_of_commands(fleet):
    assert fleet.drive("scout", "FRFLB") == 5
    assert fleet.drive("scout", "") == 0
    assert fleet.get_location("scout") == (3, 2, "north")


def test_a_blocked_move_stops_the_rest_of_the_string(fleet):
    fleet.land("mole", 2, 4, "north")
    assert fleet.drive("scout", "FFRF") == 1
    assert fleet.get_location("scout") == (2, 3, "north")
    assert fleet.get_odometer("scout") == 1
    assert fleet.get_location("mole") == (2, 4, "north")


def test_a_blocked_backward_move(fleet):
    fleet.land("mole", 2, 1, "north")
    assert fleet.drive("scout", "BL") == 0
    assert fleet.get_location("scout") == (2, 2, "north")


def test_a_move_across_the_edge_can_be_blocked():
    f = RoverFleet()
    f.land("scout", 9, 6, "east")
    f.land("mole", 0, 6, "west")
    assert f.drive("scout", "F") == 0
    assert f.drive("mole", "F") == 0
    assert f.get_location("scout") == (9, 6, "east")


def test_rovers_may_go_where_another_rover_was(fleet):
    fleet.drive("digger", "F")  # leaves (7, 5)
    fleet.land("mole", 6, 5, "east")
    assert fleet.drive("mole", "F") == 1
    assert fleet.get_rover_at(7, 5) == "mole"
    assert fleet.get_rover_at(6, 5) is None
    assert fleet.get_rover_at(8, 5) == "digger"


def test_the_odometer_counts_moves_but_not_turns(fleet):
    fleet.drive("scout", "FRRFLLB")
    fleet.drive("scout", "LLLL")
    assert fleet.get_odometer("scout") == 3
    assert fleet.get_odometer("digger") == 0


@pytest.mark.parametrize("commands", BAD_COMMANDS)
def test_invalid_command_strings_change_nothing(fleet, commands):
    before = state(fleet)
    with pytest.raises(ValueError):
        fleet.drive("scout", commands)
    assert state(fleet) == before


def test_fleets_do_not_share_rovers():
    first, second = RoverFleet(), RoverFleet()
    first.land("scout", 1, 1, "north")
    assert second.get_rovers() == []
    assert second.get_rover_at(1, 1) is None
    second.land("scout", 1, 1, "south")
    assert second.get_location("scout") == (1, 1, "south")
