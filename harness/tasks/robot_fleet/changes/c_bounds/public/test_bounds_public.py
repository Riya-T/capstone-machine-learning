"""Public checks for the c_bounds change (grid bounds). Shown to the editor,
never to the writer.

Usage (with fleet.py importable, e.g. in the sandbox):
    python -m pytest changes/c_bounds/public/test_bounds_public.py
"""

import pytest
from fleet import FleetError, RobotFleet


def test_a_robot_can_drive_up_to_the_edge():
    fl = RobotFleet(width=5, height=5)
    fl.add_robot("rover", 0, 0, "N")
    fl.run("rover", "AAAA")
    assert fl.get_position("rover") == (0, 4)
    assert fl.get_bounds() == (5, 5)


def test_leaving_the_grid_raises_and_the_robot_stays_put():
    fl = RobotFleet(width=5, height=5)
    fl.add_robot("rover", 0, 0, "N")
    with pytest.raises(FleetError):
        fl.run("rover", "AAAAA")
    assert fl.get_position("rover") == (0, 0)
    assert fl.get_command_count("rover") == 0


def test_a_start_position_outside_the_grid_is_rejected():
    fl = RobotFleet(width=5, height=5)
    with pytest.raises(ValueError):
        fl.add_robot("rover", 5, 0, "N")
    assert fl.get_robots() == []
