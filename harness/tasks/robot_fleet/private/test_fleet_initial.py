"""Hidden tests for the initial robot_fleet spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with fleet.py importable, e.g. in the sandbox):
    python -m pytest private/test_fleet_initial.py
"""

import pytest
from fleet import FleetError, RobotFleet

BAD_COMMANDS = ["X", "AAX", "a", "L R", "LR1", 5, None, ["L"]]
BAD_HEADINGS = ["n", "North", "", "NE", None, 5]
BAD_COORDS = [1.5, "1", None]


@pytest.fixture
def fleet():
    fl = RobotFleet()
    fl.add_robot("rover", 0, 0, "N")
    fl.add_robot("scout", 5, -2, "E")
    return fl


def state(fl):
    """Every pose and count, to check that a failed call changed nothing."""
    return {
        n: (fl.get_position(n), fl.get_heading(n), fl.get_command_count(n))
        for n in fl.get_robots()
    }


# --- robots -----------------------------------------------------------------


def test_a_new_robot_has_its_start_pose_and_no_commands(fleet):
    assert fleet.get_position("rover") == (0, 0)
    assert fleet.get_heading("rover") == "N"
    assert fleet.get_command_count("rover") == 0


def test_robots_are_listed_in_the_order_added():
    fl = RobotFleet()
    for name in ["c", "a", "b"]:
        fl.add_robot(name, 0, 0, "N")
    assert fl.get_robots() == ["c", "a", "b"]


def test_negative_coordinates_are_allowed():
    fl = RobotFleet()
    fl.add_robot("rover", -3, -7, "S")
    fl.run("rover", "A")
    assert fl.get_position("rover") == (-3, -8)


def test_an_empty_name_is_rejected():
    fl = RobotFleet()
    with pytest.raises(ValueError):
        fl.add_robot("", 0, 0, "N")
    assert fl.get_robots() == []


def test_a_name_already_in_use_is_rejected(fleet):
    fleet.run("rover", "A")
    before = state(fleet)
    with pytest.raises(FleetError):
        fleet.add_robot("rover", 9, 9, "S")
    assert state(fleet) == before
    assert fleet.get_robots() == ["rover", "scout"]


@pytest.mark.parametrize("heading", BAD_HEADINGS)
def test_invalid_headings_are_rejected(heading):
    fl = RobotFleet()
    with pytest.raises(ValueError):
        fl.add_robot("rover", 0, 0, heading)
    assert fl.get_robots() == []


@pytest.mark.parametrize("coord", BAD_COORDS)
def test_invalid_coordinates_are_rejected(coord):
    fl = RobotFleet()
    with pytest.raises(ValueError):
        fl.add_robot("rover", coord, 0, "N")
    with pytest.raises(ValueError):
        fl.add_robot("rover", 0, coord, "N")
    assert fl.get_robots() == []


def test_a_used_name_is_reported_before_a_bad_heading(fleet):
    with pytest.raises(FleetError):
        fleet.add_robot("rover", 0, 0, "x")


@pytest.mark.parametrize(
    "call",
    [
        lambda fl: fl.run("drone", "A"),
        lambda fl: fl.get_position("drone"),
        lambda fl: fl.get_heading("drone"),
        lambda fl: fl.get_command_count("drone"),
        lambda fl: fl.get_position(None),
        lambda fl: fl.get_position(1),
        lambda fl: fl.run(None, "A"),
    ],
)
def test_unknown_robots_raise_key_error(fleet, call):
    before = state(fleet)
    with pytest.raises(KeyError):
        call(fleet)
    assert state(fleet) == before


def test_two_robots_may_share_a_cell(fleet):
    fleet.add_robot("twin", 0, 0, "N")
    assert fleet.get_position("twin") == fleet.get_position("rover") == (0, 0)


# --- commands ---------------------------------------------------------------


def test_left_turns_go_counterclockwise(fleet):
    seen = []
    for _ in range(4):
        fleet.run("rover", "L")
        seen.append(fleet.get_heading("rover"))
    assert seen == ["W", "S", "E", "N"]
    assert fleet.get_position("rover") == (0, 0)


def test_right_turns_go_clockwise(fleet):
    seen = []
    for _ in range(4):
        fleet.run("rover", "R")
        seen.append(fleet.get_heading("rover"))
    assert seen == ["E", "S", "W", "N"]


@pytest.mark.parametrize(
    "heading, expected",
    [("N", (2, 4)), ("E", (3, 3)), ("S", (2, 2)), ("W", (1, 3))],
)
def test_advancing_moves_one_cell_in_the_facing_direction(heading, expected):
    fl = RobotFleet()
    fl.add_robot("rover", 2, 3, heading)
    fl.run("rover", "A")
    assert fl.get_position("rover") == expected
    assert fl.get_heading("rover") == heading


def test_a_longer_command_string_is_executed_in_order(fleet):
    fleet.run("scout", "AALAARRAAAL")
    assert fleet.get_position("scout") == (7, -3)
    assert fleet.get_heading("scout") == "E"
    assert fleet.get_command_count("scout") == 11


def test_runs_build_on_each_other(fleet):
    fleet.run("rover", "RA")
    fleet.run("rover", "RA")
    fleet.run("rover", "RA")
    assert fleet.get_position("rover") == (0, -1)
    assert fleet.get_heading("rover") == "W"
    assert fleet.get_command_count("rover") == 6


def test_an_empty_command_string_does_nothing(fleet):
    before = state(fleet)
    fleet.run("rover", "")
    fleet.run_all("")
    assert state(fleet) == before


def test_run_all_drives_each_robot_in_its_own_direction(fleet):
    fleet.add_robot("digger", 1, 1, "S")
    fleet.run_all("AAL")
    assert fleet.get_position("rover") == (0, 2)
    assert fleet.get_heading("rover") == "W"
    assert fleet.get_position("scout") == (7, -2)
    assert fleet.get_heading("scout") == "N"
    assert fleet.get_position("digger") == (1, -1)
    assert fleet.get_heading("digger") == "E"


def test_run_all_with_no_robots_does_nothing():
    fl = RobotFleet()
    fl.run_all("AAA")
    assert fl.get_robots() == []


@pytest.mark.parametrize("commands", BAD_COMMANDS)
def test_invalid_commands_are_rejected_and_change_nothing(fleet, commands):
    fleet.run("rover", "A")
    before = state(fleet)
    with pytest.raises(ValueError):
        fleet.run("rover", commands)
    with pytest.raises(ValueError):
        fleet.run_all(commands)
    assert state(fleet) == before


def test_an_unknown_robot_is_reported_before_bad_commands(fleet):
    with pytest.raises(KeyError):
        fleet.run("drone", "X")


def test_command_count_adds_up_over_run_and_run_all(fleet):
    fleet.run("rover", "LLA")
    fleet.run_all("RA")
    fleet.run("scout", "")
    assert fleet.get_command_count("rover") == 5
    assert fleet.get_command_count("scout") == 2


def test_fleets_do_not_share_robots():
    first, second = RobotFleet(), RobotFleet()
    first.add_robot("rover", 0, 0, "N")
    first.run("rover", "A")
    assert second.get_robots() == []
    second.add_robot("rover", 4, 4, "W")
    assert second.get_position("rover") == (4, 4)
    assert second.get_command_count("rover") == 0
