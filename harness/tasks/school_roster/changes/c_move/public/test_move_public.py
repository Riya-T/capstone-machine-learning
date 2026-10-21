"""Public checks for the c_move change (moving students, grade caps). Shown
to the editor, never to the writer.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move/public/test_move_public.py
"""

import pytest
from roster import GradeFull, Roster


def test_moved_students_join_the_end_of_the_new_grade():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 4)
    ros.add_student("cleo", 3)
    ros.move_students(["cleo", "ana"], 4)
    assert ros.get_students(3) == []
    assert ros.get_students(4) == ["ben", "cleo", "ana"]
    assert ros.get_grade("ana") == 4


def test_a_failed_move_moves_nobody():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 3)
    with pytest.raises(KeyError):
        ros.move_students(["ana", "zed", "ben"], 5)
    assert ros.get_students(3) == ["ana", "ben"]
    assert ros.get_students(5) == []


def test_a_full_grade_takes_no_more_students():
    ros = Roster(cap=2)
    assert ros.get_cap() == 2
    ros.add_student("ana", 1)
    ros.add_student("ben", 1)
    with pytest.raises(GradeFull):
        ros.add_student("cleo", 1)
    ros.add_student("cleo", 2)
    with pytest.raises(GradeFull):
        ros.move_students(["cleo"], 1)
    assert ros.get_grade("cleo") == 2
