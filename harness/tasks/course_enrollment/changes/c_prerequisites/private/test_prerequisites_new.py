"""Hidden tests for the c_prerequisites change (courses that must be
completed first). Never shown to the writer or the editor.

Usage (with enrollment.py importable, e.g. in the sandbox):
    python -m pytest changes/c_prerequisites/private/test_prerequisites_new.py
"""

import pytest
from enrollment import CourseFull, EnrollmentError, MissingPrerequisite, Registrar

COURSES = ["CS101", "MATH200", "CS201", "CS301"]
STUDENTS = ["ana", "ben", "cy"]


@pytest.fixture
def registrar():
    reg = Registrar()
    reg.add_course("CS101", 3)
    reg.add_course("MATH200", 3)
    reg.add_course("CS201", 2, prerequisites=["CS101"])
    reg.add_course("CS301", 1, prerequisites=("CS201", "MATH200"))
    for student in STUDENTS:
        reg.add_student(student)
    return reg


def state(reg):
    return (
        {c: (reg.get_roster(c), reg.get_open_seats(c)) for c in COURSES},
        {s: (reg.get_schedule(s), reg.get_completed(s)) for s in STUDENTS},
    )


def test_courses_without_prerequisites_are_open_to_anyone():
    reg = Registrar()
    reg.add_course("CS101", 2)
    reg.add_course("ART150", 2, prerequisites=[])
    reg.add_course("MUS120", 2, prerequisites=())
    reg.add_student("ana")
    for course in ["CS101", "ART150", "MUS120"]:
        reg.enroll("ana", course)
    assert reg.get_schedule("ana") == ["CS101", "ART150", "MUS120"]


def test_every_prerequisite_must_be_completed(registrar):
    registrar.record_completion("ana", "CS201")
    with pytest.raises(MissingPrerequisite):
        registrar.enroll("ana", "CS301")
    registrar.record_completion("ben", "MATH200")
    with pytest.raises(MissingPrerequisite):
        registrar.enroll("ben", "CS301")
    registrar.record_completion("ana", "MATH200")
    registrar.enroll("ana", "CS301")
    assert registrar.get_roster("CS301") == ["ana"]


def test_a_missing_prerequisite_changes_nothing(registrar):
    registrar.enroll("ben", "CS101")
    before = state(registrar)
    with pytest.raises(MissingPrerequisite):
        registrar.enroll("ben", "CS201")
    assert state(registrar) == before


def test_a_missing_prerequisite_is_reported_before_a_full_course(registrar):
    registrar.record_completion("ana", "CS201")
    registrar.record_completion("ana", "MATH200")
    registrar.enroll("ana", "CS301")  # CS301 is now full
    with pytest.raises(MissingPrerequisite):
        registrar.enroll("ben", "CS301")
    registrar.record_completion("ben", "CS201")
    registrar.record_completion("ben", "MATH200")
    with pytest.raises(CourseFull):
        registrar.enroll("ben", "CS301")


def test_unknown_ids_are_reported_before_a_missing_prerequisite(registrar):
    with pytest.raises(KeyError):
        registrar.enroll("zoe", "CS201")


def test_already_enrolled_is_still_reported(registrar):
    registrar.record_completion("ana", "CS101")
    registrar.enroll("ana", "CS201")
    with pytest.raises(EnrollmentError) as caught:
        registrar.enroll("ana", "CS201")
    assert not isinstance(caught.value, (MissingPrerequisite, CourseFull))


@pytest.mark.parametrize("prerequisites", [["CS999"], ("CS101", "CS999"), [None]])
def test_unknown_prerequisites_are_rejected(registrar, prerequisites):
    before = state(registrar)
    with pytest.raises(KeyError):
        registrar.add_course("CS401", 2, prerequisites=prerequisites)
    assert state(registrar) == before
    with pytest.raises(KeyError):
        registrar.get_roster("CS401")
    registrar.add_course("CS401", 2)  # the id is still free
    assert registrar.get_open_seats("CS401") == 2


def test_existing_add_course_checks_come_before_unknown_prerequisites(registrar):
    with pytest.raises(ValueError):
        registrar.add_course("", 2, prerequisites=["CS999"])
    with pytest.raises(ValueError):
        registrar.add_course("CS401", 0, prerequisites=["CS999"])
    with pytest.raises(EnrollmentError):
        registrar.add_course("CS101", 2, prerequisites=["CS999"])
    assert registrar.get_open_seats("CS101") == 3


@pytest.mark.parametrize(
    "call",
    [
        lambda reg: reg.record_completion("zoe", "CS101"),
        lambda reg: reg.record_completion("ana", "CS999"),
        lambda reg: reg.record_completion(None, "CS101"),
        lambda reg: reg.record_completion("ana", 1),
        lambda reg: reg.get_completed("zoe"),
        lambda reg: reg.get_completed(None),
    ],
)
def test_completions_need_known_students_and_courses(registrar, call):
    registrar.record_completion("ana", "CS101")
    before = state(registrar)
    with pytest.raises(KeyError):
        call(registrar)
    assert state(registrar) == before


def test_completions_are_listed_in_the_order_first_recorded(registrar):
    assert registrar.get_completed("ana") == []
    registrar.record_completion("ana", "MATH200")
    registrar.record_completion("ana", "CS101")
    registrar.record_completion("ana", "MATH200")
    assert registrar.get_completed("ana") == ["MATH200", "CS101"]
    assert registrar.get_completed("ben") == []


def test_recording_a_completion_leaves_enrollments_alone(registrar):
    registrar.enroll("ana", "CS101")
    registrar.record_completion("ana", "CS101")
    registrar.record_completion("ben", "MATH200")
    assert registrar.get_roster("CS101") == ["ana"]
    assert registrar.get_schedule("ana") == ["CS101"]
    assert registrar.get_schedule("ben") == []
    assert registrar.get_open_seats("CS101") == 2
    assert registrar.get_open_seats("MATH200") == 3


def test_missing_prerequisite_is_an_enrollment_error_but_not_course_full():
    assert issubclass(MissingPrerequisite, EnrollmentError)
    assert not issubclass(MissingPrerequisite, CourseFull)
