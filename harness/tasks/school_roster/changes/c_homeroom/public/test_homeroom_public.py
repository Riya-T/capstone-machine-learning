"""Public checks for the c_homeroom change (homerooms). Shown to the editor,
never to the writer.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_homeroom/public/test_homeroom_public.py
"""

import pytest
from roster import Roster, RosterError


def test_students_are_grouped_by_homeroom():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 3)
    ros.add_student("cleo", 3)
    ros.assign_homeroom("ben", "3B")
    ros.assign_homeroom("ana", "3B")
    ros.assign_homeroom("cleo", "3A")
    assert ros.get_homeroom("ana") == "3B"
    assert ros.get_homeroom_students("3B") == ["ben", "ana"]
    assert ros.get_homerooms() == ["3B", "3A"]


def test_a_homeroom_holds_one_grade_only():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 4)
    ros.assign_homeroom("ana", "3B")
    with pytest.raises(RosterError):
        ros.assign_homeroom("ben", "3B")
    assert ros.get_homeroom("ben") is None


def test_changing_grade_leaves_the_homeroom():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.assign_homeroom("ana", "3B")
    ros.move_students(["ana"], 4)
    assert ros.get_homeroom("ana") is None
    assert ros.get_homeroom_students("3B") == []
