"""Public checks for the c_disabled change (disabled robots). Shown to the
editor, never to the writer.

Usage (with fleet.py importable, e.g. in the sandbox):
    python -m pytest changes/c_disabled/public/test_disabled_public.py
"""

import pytest
from fleet import RobotDisabled, RobotFleet


def test_a_disabled_robot_cannot_be_driven():
    fl = RobotFleet()
    fl.add_robot("rover", 0, 0, "N")
    fl.disable("rover")
    assert not fl.is_enabled("rover")
    with pytest.raises(RobotDisabled):
        fl.run("rover", "A")
    assert fl.get_position("rover") == (0, 0)
    fl.enable("rover")
    fl.run("rover", "A")
    assert fl.get_position("rover") == (0, 1)


def test_run_all_skips_disabled_robots():
    fl = RobotFleet()
    fl.add_robot("rover", 0, 0, "N")
    fl.add_robot("scout", 5, 5, "E")
    fl.disable("scout")
    fl.run_all("A")
    assert fl.get_position("rover") == (0, 1)
    assert fl.get_position("scout") == (5, 5)
    assert fl.get_enabled_robots() == ["rover"]
