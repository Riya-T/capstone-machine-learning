"""Hidden tests for the c_freeze change (courses closed to enrolling for a
while). Never shown to the writer or the editor.

Usage (with enrollment.py importable, e.g. in the sandbox):
    python -m pytest changes/c_freeze/private/test_freeze_new.py
"""

import pytest
from enrollment import CourseFrozen, CourseFull, EnrollmentError, Registrar

COURSES = ["CS101", "MATH200", "ART150"]
STUDENTS = ["ana", "ben", "cy"]


@pytest.fixture
def registrar():
    reg = Registrar()
    reg.add_course("CS101", 3)
    reg.add_course("MATH200", 1)
    reg.add_course("ART150", 2)
    for student in STUDENTS:
        reg.add_student(student)
    return reg


def state(reg):
    return (
        {c: (reg.get_roster(c), reg.get_open_seats(c)) for c in COURSES},
        {s: reg.get_schedule(s) for s in STUDENTS},
    )


def test_courses_start_open(registrar):
    for course in COURSES:
        assert registrar.is_frozen(course) is False


def test_freezing_or_unfreezing_twice_is_harmless(registrar):
    registrar.freeze_course("CS101")
    registrar.freeze_course("CS101")
    assert registrar.is_frozen("CS101") is True
    registrar.unfreeze_course("CS101")
    registrar.unfreeze_course("CS101")
    assert registrar.is_frozen("CS101") is False
    registrar.unfreeze_course("MATH200")
    assert registrar.is_frozen("MATH200") is False


@pytest.mark.parametrize("method", ["freeze_course", "unfreeze_course", "is_frozen"])
@pytest.mark.parametrize("course", ["BIO110", None, 1])
def test_freeze_methods_need_a_known_course(registrar, method, course):
    with pytest.raises(KeyError):
        getattr(registrar, method)(course)


def test_enrolling_in_a_frozen_course_changes_nothing(registrar):
    registrar.enroll("ana", "CS101")
    registrar.freeze_course("CS101")
    before = state(registrar)
    with pytest.raises(CourseFrozen):
        registrar.enroll("ben", "CS101")
    assert state(registrar) == before


def test_freezing_one_course_leaves_the_others_open(registrar):
    registrar.freeze_course("CS101")
    registrar.enroll("ana", "ART150")
    registrar.enroll("ana", "MATH200")
    assert registrar.get_schedule("ana") == ["ART150", "MATH200"]
    assert registrar.is_frozen("ART150") is False


def test_frozen_is_reported_before_already_enrolled(registrar):
    registrar.enroll("ana", "CS101")
    registrar.freeze_course("CS101")
    with pytest.raises(CourseFrozen):
        registrar.enroll("ana", "CS101")


def test_frozen_is_reported_before_a_full_course(registrar):
    registrar.enroll("ana", "MATH200")
    registrar.freeze_course("MATH200")
    with pytest.raises(CourseFrozen):
        registrar.enroll("ben", "MATH200")


def test_unknown_ids_are_reported_before_frozen(registrar):
    registrar.freeze_course("CS101")
    with pytest.raises(KeyError):
        registrar.enroll("zoe", "CS101")
    with pytest.raises(KeyError):
        registrar.enroll(None, "CS101")


def test_course_frozen_is_an_enrollment_error_but_not_course_full():
    assert issubclass(CourseFrozen, EnrollmentError)
    assert not issubclass(CourseFrozen, CourseFull)


def test_everything_else_works_while_frozen(registrar):
    registrar.enroll("ben", "CS101")
    registrar.freeze_course("CS101")
    registrar.add_course("BIO110", 2)
    registrar.add_student("dee")
    registrar.enroll("dee", "BIO110")
    assert registrar.get_roster("CS101") == ["ben"]
    assert registrar.get_open_seats("CS101") == 2
    assert registrar.get_schedule("ben") == ["CS101"]
    assert registrar.get_schedule("dee") == ["BIO110"]


def test_an_unfrozen_course_fills_up_as_usual(registrar):
    registrar.freeze_course("ART150")
    registrar.unfreeze_course("ART150")
    registrar.enroll("cy", "ART150")
    registrar.enroll("ana", "ART150")
    with pytest.raises(CourseFull):
        registrar.enroll("ben", "ART150")
    with pytest.raises(EnrollmentError) as caught:
        registrar.enroll("cy", "ART150")
    assert not isinstance(caught.value, (CourseFrozen, CourseFull))
    assert registrar.get_roster("ART150") == ["cy", "ana"]
