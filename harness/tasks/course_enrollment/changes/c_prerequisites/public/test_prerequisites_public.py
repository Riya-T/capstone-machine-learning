from enrollment import EnrollmentSystem


def test_prerequisite_blocks_enrollment_until_completed():
    system = EnrollmentSystem()
    system.add_course("CS101", "Intro to Programming", 3)
    system.add_course("CS201", "Data Structures", 3, prerequisite="CS101")
    system.register_student("alice")
    assert system.enroll("alice", "CS201") is False
    system.mark_completed("alice", "CS101")
    assert system.enroll("alice", "CS201") is True


def test_course_without_prerequisite_remains_available():
    system = EnrollmentSystem()
    system.add_course("CS101", "Intro to Programming", 3)
    system.register_student("alice")
    assert system.enroll("alice", "CS101") is True
