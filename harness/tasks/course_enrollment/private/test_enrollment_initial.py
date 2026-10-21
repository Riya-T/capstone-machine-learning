"""Hidden tests for the initial course_enrollment spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with enrollment.py importable, e.g. in the sandbox):
    python -m pytest private/test_enrollment_initial.py
"""

import pytest
from enrollment import CourseFull, EnrollmentError, Registrar

COURSES = ["CS101", "MATH200", "ART150"]
STUDENTS = ["ana", "ben", "cy", "dee"]


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
    """Every roster, seat count and schedule, to check that a failed call
    changed nothing."""
    return (
        {c: (reg.get_roster(c), reg.get_open_seats(c)) for c in COURSES},
        {s: reg.get_schedule(s) for s in STUDENTS},
    )


# --- courses and students ---------------------------------------------------


def test_a_new_course_has_every_seat_open(registrar):
    assert registrar.get_roster("CS101") == []
    assert registrar.get_open_seats("CS101") == 3
    assert registrar.get_open_seats("MATH200") == 1


def test_a_new_student_has_an_empty_schedule(registrar):
    assert registrar.get_schedule("ana") == []


@pytest.mark.parametrize("capacity", [0, -1, 1.5, "3", None])
def test_invalid_capacities_are_rejected(capacity):
    reg = Registrar()
    with pytest.raises(ValueError):
        reg.add_course("BIO110", capacity)
    with pytest.raises(KeyError):
        reg.get_roster("BIO110")
    reg.add_course("BIO110", 2)  # the id is still free
    assert reg.get_open_seats("BIO110") == 2


def test_an_empty_course_id_is_rejected():
    reg = Registrar()
    with pytest.raises(ValueError):
        reg.add_course("", 5)


def test_adding_a_course_twice_is_rejected(registrar):
    registrar.enroll("ana", "MATH200")
    before = state(registrar)
    with pytest.raises(EnrollmentError):
        registrar.add_course("MATH200", 10)
    assert state(registrar) == before


def test_a_bad_capacity_is_reported_before_an_existing_course(registrar):
    with pytest.raises(ValueError):
        registrar.add_course("CS101", 0)
    assert registrar.get_open_seats("CS101") == 3


def test_an_empty_student_id_is_rejected():
    reg = Registrar()
    with pytest.raises(ValueError):
        reg.add_student("")


def test_adding_a_student_twice_is_rejected(registrar):
    registrar.enroll("ana", "CS101")
    before = state(registrar)
    with pytest.raises(EnrollmentError):
        registrar.add_student("ana")
    assert state(registrar) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda reg: reg.enroll("zoe", "CS101"),
        lambda reg: reg.enroll("ana", "BIO110"),
        lambda reg: reg.enroll(None, "CS101"),
        lambda reg: reg.enroll("ana", 1),
        lambda reg: reg.get_roster("BIO110"),
        lambda reg: reg.get_roster(None),
        lambda reg: reg.get_schedule("zoe"),
        lambda reg: reg.get_schedule(1),
        lambda reg: reg.get_open_seats("BIO110"),
        lambda reg: reg.get_open_seats(None),
    ],
)
def test_ids_that_were_not_added_raise_key_error(registrar, call):
    registrar.enroll("ana", "CS101")
    before = state(registrar)
    with pytest.raises(KeyError):
        call(registrar)
    assert state(registrar) == before


def test_students_and_courses_are_looked_up_separately(registrar):
    with pytest.raises(KeyError):
        registrar.get_schedule("CS101")
    with pytest.raises(KeyError):
        registrar.get_roster("ana")
    with pytest.raises(KeyError):
        registrar.enroll("CS101", "ana")


# --- enrolling --------------------------------------------------------------


def test_every_seat_can_be_filled(registrar):
    for student in ["ana", "ben", "cy"]:
        registrar.enroll(student, "CS101")
    assert registrar.get_open_seats("CS101") == 0
    before = state(registrar)
    with pytest.raises(CourseFull):
        registrar.enroll("dee", "CS101")
    assert state(registrar) == before


def test_a_student_can_take_several_courses(registrar):
    registrar.enroll("ben", "ART150")
    registrar.enroll("ben", "CS101")
    registrar.enroll("ben", "MATH200")
    assert registrar.get_schedule("ben") == ["ART150", "CS101", "MATH200"]
    for course in COURSES:
        assert registrar.get_roster(course) == ["ben"]


def test_each_course_has_its_own_seats(registrar):
    registrar.enroll("ana", "MATH200")
    with pytest.raises(CourseFull):
        registrar.enroll("ben", "MATH200")
    registrar.enroll("ben", "ART150")
    assert registrar.get_open_seats("MATH200") == 0
    assert registrar.get_open_seats("ART150") == 1
    assert registrar.get_open_seats("CS101") == 3


def test_enrolling_twice_changes_nothing(registrar):
    registrar.enroll("ana", "CS101")
    before = state(registrar)
    with pytest.raises(EnrollmentError):
        registrar.enroll("ana", "CS101")
    assert state(registrar) == before


def test_already_enrolled_is_reported_before_a_full_course(registrar):
    registrar.enroll("ana", "MATH200")
    with pytest.raises(EnrollmentError) as caught:
        registrar.enroll("ana", "MATH200")
    assert not isinstance(caught.value, CourseFull)


def test_an_unknown_id_is_reported_before_a_full_course(registrar):
    registrar.enroll("ana", "MATH200")
    with pytest.raises(KeyError):
        registrar.enroll("zoe", "MATH200")


def test_course_full_is_an_enrollment_error():
    assert issubclass(CourseFull, EnrollmentError)


# --- looking things up ------------------------------------------------------


def test_rosters_list_students_in_the_order_they_enrolled(registrar):
    registrar.enroll("cy", "CS101")
    registrar.enroll("ana", "CS101")
    registrar.enroll("ben", "CS101")
    assert registrar.get_roster("CS101") == ["cy", "ana", "ben"]


def test_schedules_list_courses_in_the_order_they_were_joined(registrar):
    registrar.enroll("dee", "ART150")
    registrar.enroll("ana", "CS101")
    registrar.enroll("dee", "MATH200")
    registrar.enroll("dee", "CS101")
    assert registrar.get_schedule("dee") == ["ART150", "MATH200", "CS101"]
    assert registrar.get_schedule("ana") == ["CS101"]


def test_open_seats_count_down_as_students_enroll(registrar):
    seats = []
    for student in ["ana", "ben", "cy"]:
        registrar.enroll(student, "CS101")
        seats.append(registrar.get_open_seats("CS101"))
    assert seats == [2, 1, 0]


def test_failed_calls_leave_everything_unchanged(registrar):
    registrar.enroll("ana", "MATH200")
    registrar.enroll("ben", "CS101")
    before = state(registrar)
    for call in (
        lambda: registrar.enroll("ben", "MATH200"),
        lambda: registrar.enroll("ben", "CS101"),
        lambda: registrar.enroll("zoe", "ART150"),
        lambda: registrar.add_course("CS101", 9),
        lambda: registrar.add_student("ben"),
    ):
        with pytest.raises((KeyError, EnrollmentError)):
            call()
    assert state(registrar) == before


def test_registrars_do_not_share_courses_or_students():
    first, second = Registrar(), Registrar()
    first.add_course("CS101", 1)
    first.add_student("ana")
    first.enroll("ana", "CS101")
    with pytest.raises(KeyError):
        second.get_roster("CS101")
    second.add_course("CS101", 1)
    second.add_student("ana")
    assert second.get_roster("CS101") == []
    assert second.get_schedule("ana") == []
