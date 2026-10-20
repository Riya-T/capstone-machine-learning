from enrollment import EnrollmentSystem


def test_completion_is_tracked_independently_per_student():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 3)
    system.add_course("B", "Course B", 3, prerequisite="A")
    system.register_student("alice")
    system.register_student("bob")
    system.mark_completed("alice", "A")
    assert system.enroll("alice", "B") is True
    assert system.enroll("bob", "B") is False


def test_unrelated_completion_does_not_satisfy_prerequisite():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 3)
    system.add_course("C", "Course C", 3)
    system.add_course("B", "Course B", 3, prerequisite="A")
    system.register_student("alice")
    system.mark_completed("alice", "C")
    assert system.enroll("alice", "B") is False


def test_invalid_completion_record_is_ignored():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 3)
    system.add_course("B", "Course B", 3, prerequisite="A")
    system.register_student("alice")
    system.mark_completed("unknown", "A")
    system.mark_completed("alice", "unknown")
    assert system.enroll("alice", "B") is False


def test_completed_course_does_not_require_current_enrollment():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 0)
    system.add_course("B", "Course B", 2, prerequisite="A")
    system.register_student("alice")
    system.mark_completed("alice", "A")
    assert system.enroll("alice", "B") is True


def test_missing_prerequisite_is_not_satisfied():
    system = EnrollmentSystem()
    system.add_course("B", "Course B", 2, prerequisite="A")
    system.register_student("alice")
    assert system.enroll("alice", "B") is False


def test_marking_same_course_completed_twice_is_idempotent():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 3)
    system.add_course("B", "Course B", 3, prerequisite="A")
    system.register_student("alice")
    system.mark_completed("alice", "A")
    system.mark_completed("alice", "A")
    assert system.enroll("alice", "B") is True


def test_completing_prerequisite_does_not_enroll_in_target_course():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 3)
    system.add_course("B", "Course B", 3, prerequisite="A")
    system.register_student("alice")
    system.mark_completed("alice", "A")
    assert system.courses["B"].enrolled_students == set()
    assert system.enroll("alice", "B") is True


def test_prerequisite_satisfaction_does_not_bypass_target_capacity():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 3)
    system.add_course("B", "Course B", 1, prerequisite="A")
    system.register_student("alice")
    system.register_student("bob")
    system.mark_completed("alice", "A")
    system.mark_completed("bob", "A")
    assert system.enroll("alice", "B") is True
    assert system.enroll("bob", "B") is False


def test_course_requires_itself_as_prerequisite_until_completed():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 2, prerequisite="A")
    system.register_student("alice")
    assert system.enroll("alice", "A") is False
    system.mark_completed("alice", "A")
    assert system.enroll("alice", "A") is True


def test_failed_prerequisite_attempt_does_not_take_a_seat():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 2)
    system.add_course("B", "Course B", 1, prerequisite="A")
    system.register_student("alice")
    system.register_student("bob")
    assert system.enroll("alice", "B") is False
    system.mark_completed("bob", "A")
    assert system.enroll("bob", "B") is True
