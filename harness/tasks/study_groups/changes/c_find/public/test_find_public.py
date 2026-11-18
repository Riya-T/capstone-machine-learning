"""Public checks for the c_find change (finding students). Shown to the
editor, never to the writer.

Usage (with groups.py importable, e.g. in the sandbox):
    python -m pytest changes/c_find/public/test_find_public.py
"""

import pytest
from groups import StudyGroups


@pytest.fixture
def groups():
    g = StudyGroups()
    g.add_group("red")
    g.add_group("blue")
    g.join("ann", "red")
    g.join("bob", "red")
    g.join("cid", "blue")
    return g


def test_find_student_gives_the_group_and_the_position_from_1(groups):
    assert groups.find_student("ann") == ("red", 1)
    assert groups.find_student("bob") == ("red", 2)
    assert groups.find_student("cid") == ("blue", 1)
    with pytest.raises(KeyError):
        groups.find_student("zoe")


def test_get_students_lists_them_group_by_group(groups):
    assert groups.get_students() == ["ann", "bob", "cid"]
