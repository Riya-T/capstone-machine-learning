"""Public checks for the c_prerequisites change (courses that must be
completed first). Shown to the editor, never to the writer.

Usage (with enrollment.py importable, e.g. in the sandbox):
    python -m pytest changes/c_prerequisites/public/test_prerequisites_public.py
"""

import pytest
from enrollment import MissingPrerequisite, Registrar


@pytest.fixture
def registrar():
    reg = Registrar()
    reg.add_course("CS101", 5)
    reg.add_course("CS201", 5, prerequisites=["CS101"])
    reg.add_student("ana")
    return reg


def test_a_prerequisite_must_be_completed_first(registrar):
    with pytest.raises(MissingPrerequisite):
        registrar.enroll("ana", "CS201")
    assert registrar.get_roster("CS201") == []
    registrar.record_completion("ana", "CS101")
    registrar.enroll("ana", "CS201")
    assert registrar.get_schedule("ana") == ["CS201"]


def test_completions_are_listed_without_enrolling(registrar):
    registrar.record_completion("ana", "CS101")
    assert registrar.get_completed("ana") == ["CS101"]
    assert registrar.get_schedule("ana") == []
    assert registrar.get_open_seats("CS101") == 5


def test_a_prerequisite_must_be_an_existing_course(registrar):
    with pytest.raises(KeyError):
        registrar.add_course("CS301", 5, prerequisites=["CS999"])
