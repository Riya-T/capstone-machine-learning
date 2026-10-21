"""Hidden tests for the c_distance change (distance travelled). Never shown
to the writer or the editor.

Usage (with fleet.py importable, e.g. in the sandbox):
    python -m pytest changes/c_distance/private/test_distance_new.py
"""

import pytest
from fleet import RobotFleet


@pytest.fixture
def fleet():
    fl = RobotFleet()
    fl.add_robot("rover", 0, 0, "N")
    fl.add_robot("scout", 3, -1, "E")
    return fl


def travel(fl, name):
    return (
        fl.get_distance_travelled(name),
        fl.get_displacement(name),
        fl.get_visited_cells(name),
    )


def test_a_new_robot_has_travelled_nowhere(fleet):
    assert travel(fleet, "scout") == (0, 0, [(3, -1)])


def test_turns_do_not_count_as_travel(fleet):
    fleet.run("rover", "LRLR")
    assert travel(fleet, "rover") == (0, 0, [(0, 0)])
    assert fleet.get_command_count("rover") == 4


def test_a_square_walk_returns_home(fleet):
    fleet.run("rover", "ARARARAR")
    assert fleet.get_position("rover") == (0, 0)
    assert travel(fleet, "rover") == (4, 0, [(0, 0), (0, 1), (1, 1), (1, 0)])


def test_visited_cells_are_listed_once_in_first_entered_order(fleet):
    fleet.run("rover", "AALLAAAA")
    assert fleet.get_position("rover") == (0, -2)
    assert fleet.get_visited_cells("rover") == [(0, 0), (0, 1), (0, 2), (0, -1), (0, -2)]
    assert fleet.get_distance_travelled("rover") == 6
    assert fleet.get_displacement("rover") == 2


def test_displacement_is_measured_from_the_start_not_the_origin(fleet):
    fleet.run("scout", "A")
    assert fleet.get_position("scout") == (4, -1)
    assert fleet.get_displacement("scout") == 1
    assert fleet.get_visited_cells("scout") == [(3, -1), (4, -1)]


def test_displacement_adds_both_axes(fleet):
    fleet.run("scout", "AALAAA")
    assert fleet.get_position("scout") == (5, 2)
    assert fleet.get_displacement("scout") == 5
    assert fleet.get_distance_travelled("scout") == 5


def test_travel_adds_up_over_several_runs(fleet):
    fleet.run("rover", "A")
    fleet.run("rover", "RA")
    fleet.run("rover", "")
    assert travel(fleet, "rover") == (2, 2, [(0, 0), (0, 1), (1, 1)])


def test_run_all_counts_for_every_robot(fleet):
    fleet.run_all("AA")
    assert travel(fleet, "rover") == (2, 2, [(0, 0), (0, 1), (0, 2)])
    assert travel(fleet, "scout") == (2, 2, [(3, -1), (4, -1), (5, -1)])


def test_robots_travel_independently(fleet):
    fleet.run("rover", "AAAA")
    assert travel(fleet, "scout") == (0, 0, [(3, -1)])


@pytest.mark.parametrize("commands", ["AX", "a", 5, None])
def test_a_rejected_run_adds_no_travel(fleet, commands):
    fleet.run("rover", "A")
    before = travel(fleet, "rover")
    with pytest.raises(ValueError):
        fleet.run("rover", commands)
    with pytest.raises(ValueError):
        fleet.run_all(commands)
    assert travel(fleet, "rover") == before


@pytest.mark.parametrize("method", ["get_distance_travelled", "get_displacement", "get_visited_cells"])
@pytest.mark.parametrize("name", ["drone", None, 1])
def test_unknown_robots_raise_key_error(fleet, method, name):
    with pytest.raises(KeyError):
        getattr(fleet, method)(name)
