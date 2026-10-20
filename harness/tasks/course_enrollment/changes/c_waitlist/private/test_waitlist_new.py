from enrollment import EnrollmentSystem


def test_waitlist_keeps_arrival_order_even_across_courses():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 0)
    system.add_course("B", "Course B", 0)
    for student in ("alice", "bob", "carol"):
        system.register_student(student)
    system.enroll("alice", "A")
    system.enroll("bob", "A")
    system.enroll("carol", "A")
    system.enroll("carol", "B")
    assert system.courses["A"].waitlist == ["alice", "bob", "carol"]
    assert system.courses["B"].waitlist == ["carol"]


def test_waitlisted_student_cannot_be_enrolled_a_second_time():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 0)
    system.register_student("alice")
    assert system.enroll("alice", "A") is False
    assert system.enroll("alice", "A") is False
    assert system.courses["A"].waitlist == ["alice"]


def test_unregistered_student_and_unknown_course_do_not_change_waitlist():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 0)
    assert system.enroll("unknown", "A") is False
    system.register_student("alice")
    assert system.enroll("alice", "missing") is False
    assert system.courses["A"].waitlist == []


def test_duplicate_enrollment_is_not_added_to_waitlist():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 1)
    system.register_student("alice")
    system.register_student("bob")
    assert system.enroll("alice", "A") is True
    assert system.enroll("alice", "A") is False
    assert system.courses["A"].waitlist == []
    assert system.enroll("bob", "A") is False
    assert system.courses["A"].waitlist == ["bob"]


def test_waitlisting_does_not_change_enrolled_students():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 1)
    system.register_student("alice")
    system.register_student("bob")
    assert system.enroll("alice", "A") is True
    assert system.enroll("bob", "A") is False
    assert system.courses["A"].enrolled_students == {"alice"}


def test_zero_capacity_course_queues_registered_student():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 0)
    system.register_student("alice")
    assert system.enroll("alice", "A") is False
    assert system.courses["A"].waitlist == ["alice"]


def test_students_can_waitlist_for_different_courses():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 0)
    system.add_course("B", "Course B", 0)
    system.register_student("alice")
    assert system.enroll("alice", "A") is False
    assert system.enroll("alice", "B") is False
    assert system.courses["A"].waitlist == ["alice"]
    assert system.courses["B"].waitlist == ["alice"]


def test_repeated_request_does_not_change_existing_queue_order():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 0)
    for student in ("alice", "bob", "carol"):
        system.register_student(student)
    system.enroll("alice", "A")
    system.enroll("bob", "A")
    system.enroll("carol", "A")
    system.enroll("bob", "A")
    assert system.courses["A"].waitlist == ["alice", "bob", "carol"]
