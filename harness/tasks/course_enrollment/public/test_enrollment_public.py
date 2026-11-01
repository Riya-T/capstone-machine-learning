"""Public checks for enrollment.py.

Usage (with enrollment.py importable, e.g. in the sandbox):
    python -m pytest public/test_enrollment_public.py
"""

import pytest
from enrollment import CourseFull, EnrollmentError, Registrar


@pytest.fixture
def registrar():
    reg = Registrar()
    reg.add_course("CS101", 2)
    reg.add_course("MATH200", 1)
    reg.add_student("ana")
    reg.add_student("ben")
    return reg


def test_enrolling_takes_a_seat(registrar):
    registrar.enroll("ana", "CS101")
    assert registrar.get_roster("CS101") == ["ana"]
    assert registrar.get_schedule("ana") == ["CS101"]
    assert registrar.get_open_seats("CS101") == 1


def test_a_full_course_raises_course_full(registrar):
    registrar.enroll("ana", "MATH200")
    with pytest.raises(CourseFull):
        registrar.enroll("ben", "MATH200")
    assert registrar.get_roster("MATH200") == ["ana"]
    assert registrar.get_schedule("ben") == []


def test_the_schedule_follows_the_order_of_enrolling(registrar):
    registrar.enroll("ana", "MATH200")
    registrar.enroll("ana", "CS101")
    assert registrar.get_schedule("ana") == ["MATH200", "CS101"]


def test_enrolling_twice_raises(registrar):
    registrar.enroll("ana", "CS101")
    with pytest.raises(EnrollmentError):
        registrar.enroll("ana", "CS101")
    assert registrar.get_roster("CS101") == ["ana"]
    assert registrar.get_open_seats("CS101") == 1


def test_a_negative_capacity_is_rejected():
    reg = Registrar()
    with pytest.raises(ValueError):
        reg.add_course("BIO110", -3)


def test_ids_that_were_never_added_raise_key_error(registrar):
    with pytest.raises(KeyError):
        registrar.enroll("zoe", "CS101")
    with pytest.raises(KeyError):
        registrar.get_roster("BIO110")
