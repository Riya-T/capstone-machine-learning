"""Public checks for the c_waitlist change (dropping a course, with a waiting
list that fills the freed seat). Shown to the editor, never to the writer.

Usage (with enrollment.py importable, e.g. in the sandbox):
    python -m pytest changes/c_waitlist/public/test_waitlist_public.py
"""

import pytest
from enrollment import Registrar


@pytest.fixture
def registrar():
    reg = Registrar()
    reg.add_course("MATH200", 1)
    for student in ["ana", "ben", "cy"]:
        reg.add_student(student)
    reg.enroll("ana", "MATH200")
    return reg


def test_a_full_course_can_put_students_on_its_waitlist(registrar):
    registrar.enroll("ben", "MATH200", waitlist=True)
    registrar.enroll("cy", "MATH200", waitlist=True)
    assert registrar.get_waitlist("MATH200") == ["ben", "cy"]
    assert registrar.get_roster("MATH200") == ["ana"]
    assert registrar.get_schedule("ben") == []


def test_dropping_gives_the_seat_to_the_first_in_line(registrar):
    registrar.enroll("ben", "MATH200", waitlist=True)
    registrar.enroll("cy", "MATH200", waitlist=True)
    registrar.drop("ana", "MATH200")
    assert registrar.get_roster("MATH200") == ["ben"]
    assert registrar.get_waitlist("MATH200") == ["cy"]
    assert registrar.get_schedule("ben") == ["MATH200"]
    assert registrar.get_schedule("ana") == []


def test_dropping_with_nobody_waiting_frees_the_seat(registrar):
    registrar.drop("ana", "MATH200")
    assert registrar.get_roster("MATH200") == []
    assert registrar.get_open_seats("MATH200") == 1
