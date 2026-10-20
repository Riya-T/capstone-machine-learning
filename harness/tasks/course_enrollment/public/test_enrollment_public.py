from enrollment import EnrollmentSystem


def test_student_can_enroll_in_open_course():
    system = EnrollmentSystem()
    system.add_course("CS101", "Intro to CS", 2)
    system.register_student("student_1")
    assert system.enroll("student_1", "CS101") is True


def test_multiple_students_can_enroll_when_seats_are_available():
    system = EnrollmentSystem()
    system.add_course("CS101", "Intro to CS", 3)
    system.register_student("student_1")
    system.register_student("student_2")
    assert system.enroll("student_1", "CS101") is True
    assert system.enroll("student_2", "CS101") is True


def test_student_can_enroll_in_more_than_one_course():
    system = EnrollmentSystem()
    system.add_course("CS101", "Intro to CS", 1)
    system.add_course("MATH101", "Calculus", 1)
    system.register_student("student_1")
    assert system.enroll("student_1", "CS101") is True
    assert system.enroll("student_1", "MATH101") is True
