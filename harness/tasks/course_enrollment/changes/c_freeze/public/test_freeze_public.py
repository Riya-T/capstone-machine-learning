"""Public checks for the c_freeze change (courses closed to enrolling for a
while). Shown to the editor, never to the writer.

Usage (with enrollment.py importable, e.g. in the sandbox):
    python -m pytest changes/c_freeze/public/test_freeze_public.py
"""

import pytest
from enrollment import CourseFrozen, Registrar


@pytest.fixture
def registrar():
    reg = Registrar()
    reg.add_course("CS101", 3)
    reg.add_student("ana")
    reg.add_student("ben")
    return reg


def test_a_frozen_course_refuses_new_students(registrar):
    registrar.freeze_course("CS101")
    assert registrar.is_frozen("CS101")
    with pytest.raises(CourseFrozen):
        registrar.enroll("ana", "CS101")
    registrar.unfreeze_course("CS101")
    registrar.enroll("ana", "CS101")
    assert registrar.get_roster("CS101") == ["ana"]


def test_enrolled_students_keep_their_seats_while_frozen(registrar):
    registrar.enroll("ben", "CS101")
    registrar.freeze_course("CS101")
    assert registrar.get_roster("CS101") == ["ben"]
    assert registrar.get_open_seats("CS101") == 2
