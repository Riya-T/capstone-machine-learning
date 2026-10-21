"""Public checks for fleet.py.

Usage (with fleet.py importable, e.g. in the sandbox):
    python -m pytest public/test_fleet_public.py
"""

import pytest
from fleet import RobotFleet


@pytest.fixture
def fleet():
    fl = RobotFleet()
    fl.add_robot("rover", 0, 0, "N")
    fl.add_robot("scout", 5, -2, "E")
    return fl


def test_a_new_robot_reports_where_it_was_placed(fleet):
    assert fleet.get_position("scout") == (5, -2)
    assert fleet.get_heading("scout") == "E"
    assert fleet.get_robots() == ["rover", "scout"]
    assert fleet.get_command_count("scout") == 0


def test_run_moves_and_turns_the_robot(fleet):
    fleet.run("rover", "AARAL")
    assert fleet.get_position("rover") == (1, 2)
    assert fleet.get_heading("rover") == "N"
    assert fleet.get_command_count("rover") == 5


def test_turning_left_from_north_faces_west(fleet):
    fleet.run("rover", "L")
    assert fleet.get_heading("rover") == "W"
    fleet.run("rover", "A")
    assert fleet.get_position("rover") == (-1, 0)


def test_run_all_drives_every_robot(fleet):
    fleet.run_all("A")
    assert fleet.get_position("rover") == (0, 1)
    assert fleet.get_position("scout") == (6, -2)


def test_unknown_robot_raises_key_error(fleet):
    with pytest.raises(KeyError):
        fleet.get_position("drone")
    with pytest.raises(KeyError):
        fleet.run("drone", "A")


def test_invalid_commands_raise_value_error(fleet):
    with pytest.raises(ValueError):
        fleet.run("rover", "X")
    with pytest.raises(ValueError):
        fleet.run_all("a")
