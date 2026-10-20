from enrollment import EnrollmentSystem


def test_full_course_queues_student_in_order():
    system = EnrollmentSystem()
    system.add_course("BIO101", "Biology", 1)
    system.register_student("alice")
    system.register_student("bob")
    system.register_student("carol")
    assert system.enroll("alice", "BIO101") is True
    assert system.enroll("bob", "BIO101") is False
    assert system.enroll("carol", "BIO101") is False
    assert system.courses["BIO101"].waitlist == ["bob", "carol"]


def test_duplicate_waitlist_request_is_not_added_again():
    system = EnrollmentSystem()
    system.add_course("BIO101", "Biology", 0)
    system.register_student("alice")
    assert system.enroll("alice", "BIO101") is False
    assert system.enroll("alice", "BIO101") is False
    assert system.courses["BIO101"].waitlist == ["alice"]
