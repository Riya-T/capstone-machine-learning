import pytest

from enrollment import EnrollmentSystem


def test_course_creation_and_student_registration():
    system = EnrollmentSystem()
    system.add_course("MATH201", "Linear Algebra", 2)
    system.register_student("alice")
    assert system.courses["MATH201"].title == "Linear Algebra"
    assert "alice" in system.students


def test_registered_student_can_enroll():
    system = EnrollmentSystem()
    system.add_course("MATH201", "Linear Algebra", 2)
    system.register_student("alice")
    assert system.enroll("alice", "MATH201") is True
    assert "alice" in system.courses["MATH201"].enrolled_students


def test_course_capacity_is_enforced():
    system = EnrollmentSystem()
    system.add_course("MATH201", "Linear Algebra", 1)
    system.register_student("alice")
    system.register_student("bob")
    assert system.enroll("alice", "MATH201") is True
    assert system.enroll("bob", "MATH201") is False
    assert system.courses["MATH201"].enrolled_students == {"alice"}


def test_duplicate_enrollment_is_rejected():
    system = EnrollmentSystem()
    system.add_course("CS101", "Programming", 3)
    system.register_student("alice")
    assert system.enroll("alice", "CS101") is True
    assert system.enroll("alice", "CS101") is False
    assert system.courses["CS101"].enrolled_students == {"alice"}


def test_unregistered_student_and_unknown_course_are_rejected():
    system = EnrollmentSystem()
    system.add_course("CS101", "Programming", 3)
    system.register_student("alice")
    assert system.enroll("bob", "CS101") is False
    assert system.enroll("alice", "MISSING") is False
    assert system.courses["CS101"].enrolled_students == set()


def test_capacity_zero_never_allows_enrollment():
    system = EnrollmentSystem()
    system.add_course("FULL", "No seats", 0)
    system.register_student("alice")
    assert system.enroll("alice", "FULL") is False


@pytest.mark.parametrize("capacity", [-1, -10])
def test_negative_capacity_is_rejected_without_replacing_existing_course(capacity):
    system = EnrollmentSystem()
    system.add_course("CS101", "Programming", 2)
    with pytest.raises(ValueError):
        system.add_course("CS101", "Replacement", capacity)
    assert system.courses["CS101"].title == "Programming"
    assert system.courses["CS101"].capacity == 2


def test_repeated_registration_is_idempotent():
    system = EnrollmentSystem()
    system.register_student("alice")
    system.register_student("alice")
    assert len(system.students) == 1


def test_capacity_is_independent_for_each_course():
    system = EnrollmentSystem()
    system.add_course("CS101", "Programming", 1)
    system.add_course("MATH101", "Calculus", 1)
    system.register_student("alice")
    system.register_student("bob")
    assert system.enroll("alice", "CS101") is True
    assert system.enroll("bob", "CS101") is False
    assert system.enroll("bob", "MATH101") is True


@pytest.mark.parametrize("capacity", [1.5, "2"])
def test_non_integer_capacity_is_rejected(capacity):
    system = EnrollmentSystem()
    with pytest.raises(ValueError):
        system.add_course("CS101", "Programming", capacity)
    assert "CS101" not in system.courses


def test_readding_course_code_replaces_course_record():
    system = EnrollmentSystem()
    system.add_course("CS101", "Old title", 2)
    system.add_course("CS101", "New title", 1)
    course = system.courses["CS101"]
    assert course.title == "New title"
    assert course.capacity == 1
    assert course.enrolled_students == set()


def test_registering_student_again_does_not_clear_enrollment():
    system = EnrollmentSystem()
    system.add_course("CS101", "Programming", 2)
    system.register_student("alice")
    assert system.enroll("alice", "CS101") is True
    system.register_student("alice")
    assert system.courses["CS101"].enrolled_students == {"alice"}


def test_empty_course_and_empty_student_set_are_valid():
    system = EnrollmentSystem()
    system.add_course("CS101", "Programming", 0)
    assert system.courses["CS101"].enrolled_students == set()
    assert system.students == set()


def test_unknown_student_attempt_does_not_consume_a_seat():
    system = EnrollmentSystem()
    system.add_course("CS101", "Programming", 1)
    assert system.enroll("alice", "CS101") is False
    system.register_student("bob")
    assert system.enroll("bob", "CS101") is True
