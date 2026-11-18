"""Public checks for the c_lock change (locked groups). Shown to the editor,
never to the writer.

Usage (with groups.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/public/test_lock_public.py
"""

import pytest
from groups import GroupLocked, StudyGroups


@pytest.fixture
def groups():
    g = StudyGroups()
    g.add_group("red")
    g.add_group("blue")
    g.join("ann", "red")
    return g


def test_nobody_joins_a_locked_group(groups):
    groups.lock_group("red")
    assert groups.get_locked() == ["red"]
    with pytest.raises(GroupLocked):
        groups.join("bob", "red")
    assert groups.get_members("red") == ["ann"]
    groups.unlock_group("red")
    groups.join("bob", "red")
    assert groups.get_members("red") == ["ann", "bob"]


def test_nobody_leaves_a_locked_group(groups):
    groups.lock_group("red")
    with pytest.raises(GroupLocked):
        groups.leave("ann")
    assert groups.get_members("red") == ["ann"]
