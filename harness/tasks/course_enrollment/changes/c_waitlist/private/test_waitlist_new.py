"""Hidden tests for the c_waitlist change (dropping a course, with a waiting
list that fills the freed seat). Never shown to the writer or the editor.

Usage (with enrollment.py importable, e.g. in the sandbox):
    python -m pytest changes/c_waitlist/private/test_waitlist_new.py
"""

import pytest
from enrollment import CourseFull, EnrollmentError, MissingPrerequisite, Registrar

COURSES = ["CS101", "MATH200", "ART150"]
STUDENTS = ["ana", "ben", "cy", "dee"]


@pytest.fixture
def registrar():
    reg = Registrar()
    reg.add_course("CS101", 2)
    reg.add_course("MATH200", 1)
    reg.add_course("ART150", 3)
    for student in STUDENTS:
        reg.add_student(student)
    return reg


def state(reg):
    return (
        {c: (reg.get_roster(c), reg.get_waitlist(c), reg.get_open_seats(c)) for c in COURSES},
        {s: (reg.get_schedule(s), reg.get_completed(s)) for s in STUDENTS},
    )


def test_with_an_open_seat_waitlist_true_simply_enrolls(registrar):
    assert registrar.get_waitlist("CS101") == []
    registrar.enroll("ana", "CS101", waitlist=True)
    assert registrar.get_roster("CS101") == ["ana"]
    assert registrar.get_waitlist("CS101") == []
    assert registrar.get_open_seats("CS101") == 1


def test_a_full_course_still_raises_without_waitlist_true(registrar):
    registrar.enroll("ana", "MATH200")
    before = state(registrar)
    with pytest.raises(CourseFull):
        registrar.enroll("ben", "MATH200")
    with pytest.raises(CourseFull):
        registrar.enroll("ben", "MATH200", waitlist=False)
    assert state(registrar) == before


def test_waiting_students_are_queued_first_come_first_served(registrar):
    registrar.enroll("ana", "MATH200")
    for student in ["dee", "ben", "cy"]:
        registrar.enroll(student, "MATH200", waitlist=True)
    assert registrar.get_waitlist("MATH200") == ["dee", "ben", "cy"]
    assert registrar.get_roster("MATH200") == ["ana"]
    assert registrar.get_open_seats("MATH200") == 0
    for student in ["dee", "ben", "cy"]:
        assert registrar.get_schedule(student) == []


@pytest.mark.parametrize("waitlist", [False, True])
def test_a_waiting_student_cannot_ask_again(registrar, waitlist):
    registrar.enroll("ana", "MATH200")
    registrar.enroll("ben", "MATH200", waitlist=True)
    before = state(registrar)
    with pytest.raises(EnrollmentError) as caught:
        registrar.enroll("ben", "MATH200", waitlist=waitlist)
    assert not isinstance(caught.value, CourseFull)
    assert state(registrar) == before


def test_an_enrolled_student_cannot_join_the_waitlist(registrar):
    registrar.enroll("ana", "MATH200")
    before = state(registrar)
    with pytest.raises(EnrollmentError) as caught:
        registrar.enroll("ana", "MATH200", waitlist=True)
    assert not isinstance(caught.value, CourseFull)
    assert state(registrar) == before


def test_joining_a_waitlist_needs_the_prerequisites(registrar):
    registrar.add_course("CS201", 1, prerequisites=["CS101"])
    registrar.record_completion("ana", "CS101")
    registrar.enroll("ana", "CS201")
    with pytest.raises(MissingPrerequisite):
        registrar.enroll("ben", "CS201", waitlist=True)
    assert registrar.get_waitlist("CS201") == []
    registrar.record_completion("ben", "CS101")
    registrar.enroll("ben", "CS201", waitlist=True)
    assert registrar.get_waitlist("CS201") == ["ben"]


def test_the_promoted_student_goes_to_the_end_of_roster_and_schedule(registrar):
    registrar.enroll("ana", "CS101")
    registrar.enroll("ben", "CS101")
    registrar.enroll("cy", "ART150")
    registrar.enroll("cy", "CS101", waitlist=True)
    registrar.enroll("dee", "CS101", waitlist=True)
    registrar.drop("ana", "CS101")
    assert registrar.get_roster("CS101") == ["ben", "cy"]
    assert registrar.get_waitlist("CS101") == ["dee"]
    assert registrar.get_schedule("cy") == ["ART150", "CS101"]
    assert registrar.get_open_seats("CS101") == 0
    registrar.drop("ben", "CS101")
    assert registrar.get_roster("CS101") == ["cy", "dee"]
    assert registrar.get_waitlist("CS101") == []


def test_dropping_one_course_keeps_the_others(registrar):
    registrar.enroll("ana", "ART150")
    registrar.enroll("ana", "CS101")
    registrar.enroll("ana", "MATH200")
    registrar.drop("ana", "CS101")
    assert registrar.get_schedule("ana") == ["ART150", "MATH200"]
    assert registrar.get_roster("CS101") == []
    assert registrar.get_open_seats("CS101") == 2
    assert registrar.get_roster("ART150") == ["ana"]


def test_leaving_the_waitlist_changes_nothing_else(registrar):
    registrar.enroll("ana", "MATH200")
    for student in ["ben", "cy", "dee"]:
        registrar.enroll(student, "MATH200", waitlist=True)
    registrar.drop("cy", "MATH200")
    assert registrar.get_waitlist("MATH200") == ["ben", "dee"]
    assert registrar.get_roster("MATH200") == ["ana"]
    assert registrar.get_open_seats("MATH200") == 0
    assert registrar.get_schedule("cy") == []


@pytest.mark.parametrize(
    "call, error",
    [
        (lambda reg: reg.drop("zoe", "MATH200"), KeyError),
        (lambda reg: reg.drop("ana", "BIO110"), KeyError),
        (lambda reg: reg.drop(None, "MATH200"), KeyError),
        (lambda reg: reg.drop("zoe", "BIO110"), KeyError),
        (lambda reg: reg.drop("cy", "MATH200"), EnrollmentError),
        (lambda reg: reg.drop("ben", "CS101"), EnrollmentError),
        (lambda reg: reg.get_waitlist("BIO110"), KeyError),
        (lambda reg: reg.get_waitlist(None), KeyError),
    ],
)
def test_bad_calls_raise_and_change_nothing(registrar, call, error):
    registrar.enroll("ana", "MATH200")
    registrar.enroll("ben", "MATH200", waitlist=True)
    before = state(registrar)
    with pytest.raises(error):
        call(registrar)
    assert state(registrar) == before


def test_a_dropped_student_can_come_back(registrar):
    registrar.enroll("ana", "CS101")
    registrar.enroll("ben", "CS101")
    registrar.drop("ana", "CS101")
    registrar.enroll("ana", "CS101")
    assert registrar.get_roster("CS101") == ["ben", "ana"]
    registrar.enroll("cy", "CS101", waitlist=True)
    registrar.drop("cy", "CS101")
    registrar.enroll("dee", "CS101", waitlist=True)
    registrar.enroll("cy", "CS101", waitlist=True)
    assert registrar.get_waitlist("CS101") == ["dee", "cy"]


def test_dropping_keeps_completed_courses(registrar):
    registrar.record_completion("ana", "ART150")
    registrar.enroll("ana", "CS101")
    registrar.drop("ana", "CS101")
    assert registrar.get_completed("ana") == ["ART150"]
