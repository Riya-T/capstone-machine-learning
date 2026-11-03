"""Public checks for the c_distance change (distance travelled). Shown to the
editor, never to the writer.

Usage (with fleet.py importable, e.g. in the sandbox):
    python -m pytest changes/c_distance/public/test_distance_public.py
"""

from fleet import RobotFleet


def test_distance_counts_moves_and_displacement_measures_the_result():
    fl = RobotFleet()
    fl.add_robot("rover", 0, 0, "N")
    fl.run("rover", "MMRM")
    assert fl.get_distance_travelled("rover") == 3
    assert fl.get_displacement("rover") == 3
    assert fl.get_visited_cells("rover") == [(0, 0), (0, 1), (0, 2), (1, 2)]


def test_the_command_count_still_counts_turns_but_the_distance_does_not():
    fl = RobotFleet()
    fl.add_robot("rover", 0, 0, "N")
    fl.run("rover", "MMRM")
    assert fl.get_command_count("rover") == 4  # every command, as before
    assert fl.get_distance_travelled("rover") == 3  # only the moves


def test_turning_only_travels_nowhere():
    fl = RobotFleet()
    fl.add_robot("rover", 2, 3, "N")
    fl.run("rover", "LLRR")
    assert fl.get_distance_travelled("rover") == 0
    assert fl.get_displacement("rover") == 0
    assert fl.get_visited_cells("rover") == [(2, 3)]
    assert fl.get_command_count("rover") == 4


def test_going_back_adds_distance_but_not_displacement():
    fl = RobotFleet()
    fl.add_robot("rover", 0, 0, "N")
    fl.run("rover", "MRRM")
    assert fl.get_distance_travelled("rover") == 2
    assert fl.get_displacement("rover") == 0
    assert fl.get_visited_cells("rover") == [(0, 0), (0, 1)]
