import pytest

from enrollment import EnrollmentSystem


def test_every_enroll_call_raises_while_frozen():
    system = EnrollmentSystem()
    system.set_freeze(True)
    with pytest.raises(RuntimeError):
        system.enroll("unknown", "missing")


def test_frozen_state_blocks_enrollment_without_changing_membership():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 2)
    system.register_student("alice")
    system.set_freeze(True)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            system.enroll("alice", "A")
    assert system.courses["A"].enrolled_students == set()


def test_course_and_student_setup_is_allowed_while_frozen():
    system = EnrollmentSystem()
    system.set_freeze(True)
    system.add_course("A", "Course A", 1)
    system.register_student("alice")
    system.set_freeze(False)
    assert system.enroll("alice", "A") is True


def test_freeze_can_be_enabled_again_after_unfreezing():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 2)
    system.register_student("alice")
    system.set_freeze(True)
    system.set_freeze(False)
    assert system.enroll("alice", "A") is True
    system.set_freeze(True)
    with pytest.raises(RuntimeError):
        system.enroll("bob", "A")


def test_system_starts_unfrozen():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 1)
    system.register_student("alice")
    assert system.enroll("alice", "A") is True


def test_freezing_does_not_remove_existing_enrollments():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 2)
    system.register_student("alice")
    assert system.enroll("alice", "A") is True
    system.set_freeze(True)
    assert system.courses["A"].enrolled_students == {"alice"}


def test_setting_freeze_true_repeatedly_keeps_enrollment_blocked():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 2)
    system.register_student("alice")
    system.set_freeze(True)
    system.set_freeze(True)
    with pytest.raises(RuntimeError):
        system.enroll("alice", "A")


def test_setting_freeze_false_when_already_unfrozen_is_safe():
    system = EnrollmentSystem()
    system.add_course("A", "Course A", 1)
    system.register_student("alice")
    system.set_freeze(False)
    assert system.enroll("alice", "A") is True


def test_freeze_state_is_not_shared_between_systems():
    frozen = EnrollmentSystem()
    active = EnrollmentSystem()
    frozen.add_course("A", "Course A", 1)
    active.add_course("A", "Course A", 1)
    frozen.register_student("alice")
    active.register_student("alice")
    frozen.set_freeze(True)
    with pytest.raises(RuntimeError):
        frozen.enroll("alice", "A")
    assert active.enroll("alice", "A") is True
