"""Hidden tests for the c_bounds change (grid bounds). Never shown to the
writer or the editor.

Usage (with fleet.py importable, e.g. in the sandbox):
    python -m pytest changes/c_bounds/private/test_bounds_new.py
"""

import pytest
from fleet import FleetError, RobotFleet

BAD_BOUNDS = [0, -1, 1.5, "3", True]


@pytest.fixture
def fleet():
    fl = RobotFleet(width=4, height=5)
    fl.add_robot("rover", 0, 0, "N")
    fl.add_robot("scout", 3, 4, "E")  # in the far corner, facing out
    return fl


def state(fl):
    return {
        n: (fl.get_position(n), fl.get_heading(n), fl.get_command_count(n))
        for n in fl.get_robots()
    }


def test_bounds_default_to_none_and_the_grid_stays_endless():
    fl = RobotFleet()
    assert fl.get_bounds() == (None, None)
    fl.add_robot("rover", 0, 0, "S")
    fl.run("rover", "AAA")
    assert fl.get_position("rover") == (0, -3)


@pytest.mark.parametrize("bound", BAD_BOUNDS)
def test_invalid_bounds_are_rejected(bound):
    with pytest.raises(ValueError):
        RobotFleet(width=bound)
    with pytest.raises(ValueError):
        RobotFleet(height=bound)


def test_a_bound_in_one_direction_leaves_the_other_free():
    fl = RobotFleet(width=3)
    assert fl.get_bounds() == (3, None)
    fl.add_robot("rover", 0, 0, "S")
    fl.run("rover", "AAAA")
    assert fl.get_position("rover") == (0, -4)
    fl.run("rover", "R")  # now facing W at x = 0
    with pytest.raises(FleetError):
        fl.run("rover", "A")
    assert fl.get_position("rover") == (0, -4)


def test_the_last_cell_is_inside_and_the_next_is_not(fleet):
    fleet.run("rover", "RAAA")
    assert fleet.get_position("rover") == (3, 0)
    with pytest.raises(FleetError):
        fleet.run("rover", "A")
    assert fleet.get_position("rover") == (3, 0)
    assert fleet.get_command_count("rover") == 4


def test_leaving_and_coming_back_is_still_rejected(fleet):
    before = state(fleet)
    with pytest.raises(FleetError):
        fleet.run("scout", "ALLA")
    assert state(fleet) == before


def test_a_rejected_run_changes_neither_heading_nor_count(fleet):
    before = state(fleet)
    with pytest.raises(FleetError):
        fleet.run("scout", "RRRA")  # three turns, then off the north edge
    assert state(fleet) == before


def test_run_all_changes_nothing_if_any_robot_would_leave(fleet):
    before = state(fleet)
    with pytest.raises(FleetError):
        fleet.run_all("A")  # rover could move north, scout would leave
    assert state(fleet) == before


def test_run_all_moves_every_robot_when_all_stay_inside(fleet):
    fleet.run_all("RA")
    assert fleet.get_position("rover") == (1, 0)
    assert fleet.get_heading("rover") == "E"
    assert fleet.get_position("scout") == (3, 3)
    assert fleet.get_heading("scout") == "S"
    assert fleet.get_command_count("scout") == 2


@pytest.mark.parametrize("x, y", [(4, 0), (0, 5), (-1, 0), (0, -1), (9, 9)])
def test_start_positions_outside_the_grid_are_rejected(fleet, x, y):
    with pytest.raises(ValueError):
        fleet.add_robot("drone", x, y, "N")
    assert fleet.get_robots() == ["rover", "scout"]


def test_edge_starts_are_accepted_and_a_used_name_is_reported_first(fleet):
    fleet.add_robot("a", 0, 4, "N")
    fleet.add_robot("b", 3, 0, "N")
    assert fleet.get_robots() == ["rover", "scout", "a", "b"]
    with pytest.raises(FleetError):
        fleet.add_robot("rover", 9, 9, "N")


def test_bad_commands_are_reported_before_leaving_the_grid(fleet):
    before = state(fleet)
    with pytest.raises(ValueError):
        fleet.run("scout", "AX")
    with pytest.raises(ValueError):
        fleet.run_all("AX")
    assert state(fleet) == before


def test_an_unknown_robot_is_reported_before_leaving_the_grid(fleet):
    with pytest.raises(KeyError):
        fleet.run("drone", "A")
