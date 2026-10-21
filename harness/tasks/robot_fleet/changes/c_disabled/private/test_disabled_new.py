"""Hidden tests for the c_disabled change (disabled robots). Never shown to
the writer or the editor.

Usage (with fleet.py importable, e.g. in the sandbox):
    python -m pytest changes/c_disabled/private/test_disabled_new.py
"""

import pytest
from fleet import FleetError, RobotDisabled, RobotFleet


@pytest.fixture
def fleet():
    fl = RobotFleet()
    fl.add_robot("rover", 0, 0, "N")
    fl.add_robot("scout", 5, 5, "E")
    fl.add_robot("digger", -2, 3, "S")
    return fl


def state(fl):
    return {
        n: (fl.get_position(n), fl.get_heading(n), fl.get_command_count(n))
        for n in fl.get_robots()
    }


def test_robots_start_enabled(fleet):
    assert all(fleet.is_enabled(n) for n in fleet.get_robots())
    assert fleet.get_enabled_robots() == ["rover", "scout", "digger"]
    assert issubclass(RobotDisabled, FleetError)


def test_disabling_or_enabling_twice_is_harmless(fleet):
    fleet.disable("scout")
    fleet.disable("scout")
    assert not fleet.is_enabled("scout")
    fleet.enable("scout")
    fleet.enable("scout")
    assert fleet.is_enabled("scout")
    assert fleet.get_enabled_robots() == ["rover", "scout", "digger"]


@pytest.mark.parametrize("method", ["disable", "enable", "is_enabled"])
@pytest.mark.parametrize("name", ["drone", None, 1])
def test_unknown_robots_raise_key_error(fleet, method, name):
    with pytest.raises(KeyError):
        getattr(fleet, method)(name)


def test_enabled_robots_keep_the_order_added(fleet):
    fleet.disable("rover")
    assert fleet.get_enabled_robots() == ["scout", "digger"]
    fleet.enable("rover")
    assert fleet.get_enabled_robots() == ["rover", "scout", "digger"]
    assert fleet.get_robots() == ["rover", "scout", "digger"]


def test_running_a_disabled_robot_changes_nothing(fleet):
    fleet.run("rover", "A")
    fleet.disable("rover")
    before = state(fleet)
    with pytest.raises(RobotDisabled):
        fleet.run("rover", "RAA")
    assert state(fleet) == before


def test_run_all_drives_only_the_enabled_robots(fleet):
    fleet.run("scout", "A")
    fleet.disable("scout")
    fleet.run_all("AL")
    assert fleet.get_position("rover") == (0, 1)
    assert fleet.get_heading("rover") == "W"
    assert fleet.get_position("digger") == (-2, 2)
    assert fleet.get_heading("digger") == "E"
    assert fleet.get_position("scout") == (6, 5)
    assert fleet.get_heading("scout") == "E"
    assert fleet.get_command_count("scout") == 1


def test_run_all_with_every_robot_disabled_does_nothing(fleet):
    for name in fleet.get_robots():
        fleet.disable(name)
    before = state(fleet)
    fleet.run_all("AAA")
    assert state(fleet) == before


def test_invalid_commands_still_raise_when_all_are_disabled(fleet):
    for name in fleet.get_robots():
        fleet.disable(name)
    with pytest.raises(ValueError):
        fleet.run_all("X")
    with pytest.raises(ValueError):
        fleet.run("rover", "X")


def test_a_disabled_robot_still_reports_its_state(fleet):
    fleet.run("digger", "AA")
    fleet.disable("digger")
    assert fleet.get_position("digger") == (-2, 1)
    assert fleet.get_heading("digger") == "S"
    assert fleet.get_command_count("digger") == 2
    fleet.enable("digger")
    fleet.disable("digger")
    assert fleet.get_command_count("digger") == 2  # not commands


def test_key_error_and_value_error_come_before_disabled(fleet):
    fleet.disable("rover")
    with pytest.raises(KeyError):
        fleet.run("drone", "A")
    with pytest.raises(ValueError):
        fleet.run("rover", "X")


def test_disabled_comes_before_other_fleet_errors():
    fl = RobotFleet(width=2, height=2)
    fl.add_robot("rover", 1, 1, "N")  # facing the edge
    fl.disable("rover")
    with pytest.raises(RobotDisabled):
        fl.run("rover", "A")


def test_a_disabled_robot_never_blocks_run_all():
    fl = RobotFleet(width=2, height=2)
    fl.add_robot("rover", 0, 0, "N")
    fl.add_robot("scout", 1, 1, "N")  # would leave the grid
    fl.disable("scout")
    fl.run_all("A")
    assert fl.get_position("rover") == (0, 1)
    assert fl.get_position("scout") == (1, 1)
