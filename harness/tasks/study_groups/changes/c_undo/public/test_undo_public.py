"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with groups.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from groups import GroupError, StudyGroups


@pytest.fixture
def groups():
    g = StudyGroups()
    g.add_group("red")
    g.add_group("blue")
    return g


def test_undo_takes_back_the_last_join(groups):
    groups.join("ann", "red")
    groups.join("bob", "red")
    groups.undo()
    assert groups.get_members("red") == ["ann"]
    groups.undo()
    assert groups.get_members("red") == []


def test_undo_takes_back_a_swap(groups):
    groups.join("ann", "red")
    groups.join("bob", "red")
    groups.swap_students("ann", "bob")
    groups.undo()
    assert groups.get_members("red") == ["ann", "bob"]


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(GroupError):
        StudyGroups().undo()
