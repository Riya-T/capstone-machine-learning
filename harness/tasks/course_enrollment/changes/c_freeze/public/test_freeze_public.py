import pytest

from enrollment import EnrollmentSystem


def test_frozen_enrollment_raises_without_enrolling_student():
    system = EnrollmentSystem()
    system.add_course("ENG101", "Composition", 2)
    system.register_student("alice")
    system.set_freeze(True)
    with pytest.raises(RuntimeError):
        system.enroll("alice", "ENG101")
    assert system.courses["ENG101"].enrolled_students == set()


def test_unfreezing_restores_normal_enrollment():
    system = EnrollmentSystem()
    system.add_course("ENG101", "Composition", 2)
    system.register_student("alice")
    system.set_freeze(True)
    system.set_freeze(False)
    assert system.enroll("alice", "ENG101") is True
