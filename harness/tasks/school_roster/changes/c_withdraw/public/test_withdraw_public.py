"""Public checks for the c_withdraw change (withdrawing and reinstating
students). Shown to the editor, never to the writer.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_withdraw/public/test_withdraw_public.py
"""

import pytest
from roster import Roster


def test_a_withdrawn_student_leaves_their_grade():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 3)
    ros.withdraw_student("ana")
    assert ros.get_students(3) == ["ben"]
    assert ros.get_withdrawn() == ["ana"]
    with pytest.raises(KeyError):
        ros.get_grade("ana")


def test_a_reinstated_student_returns_to_the_end_of_their_grade():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 3)
    ros.withdraw_student("ana")
    ros.reinstate_student("ana")
    assert ros.get_students(3) == ["ben", "ana"]
    assert ros.get_withdrawn() == []


def test_withdrawing_twice_raises():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.withdraw_student("ana")
    with pytest.raises(KeyError):
        ros.withdraw_student("ana")
