"""Hidden tests for the c_lock change (locked groups). Never shown to the
writer or the editor. They call only the spec's methods and this change's
own, never undo.

Usage (with groups.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/private/test_lock_new.py
"""

import pytest
from groups import GroupError, GroupLocked, StudyGroups


@pytest.fixture
def groups():
    g = StudyGroups()
    for name in ["red", "blue", "green"]:
        g.add_group(name)
    for student in ["ann", "bob", "cid"]:
        g.join(student, "red")
    g.join("dan", "blue")
    g.join("eve", "blue")
    return g


def state(g):
    return [(name, g.get_members(name)) for name in g.get_groups()]


# --- locking and unlocking --------------------------------------------------------


def test_new_groups_are_unlocked(groups):
    assert groups.get_locked() == []


def test_locked_groups_are_listed_in_group_order(groups):
    groups.lock_group("green")
    groups.lock_group("red")
    assert groups.get_locked() == ["red", "green"]
    groups.unlock_group("red")
    assert groups.get_locked() == ["green"]


def test_locking_twice_then_unlocking_once_unlocks(groups):
    groups.lock_group("red")
    groups.lock_group("red")
    groups.unlock_group("red")
    assert groups.get_locked() == []
    groups.join("fay", "red")
    assert groups.get_members("red") == ["ann", "bob", "cid", "fay"]


def test_unlocking_a_group_that_is_not_locked_does_nothing(groups):
    groups.unlock_group("red")
    groups.lock_group("blue")
    groups.unlock_group("green")
    assert groups.get_locked() == ["blue"]
    with pytest.raises(GroupLocked):
        groups.join("fay", "blue")


@pytest.mark.parametrize(
    "call",
    [
        lambda g: g.lock_group("pink"),
        lambda g: g.unlock_group("pink"),
        lambda g: g.lock_group("green"),  # dissolved below
        lambda g: g.unlock_group("green"),
    ],
)
def test_groups_not_in_use_raise_key_error(groups, call):
    groups.dissolve_group("green", "blue")
    with pytest.raises(KeyError):
        call(groups)


def test_locking_changes_no_members(groups):
    before = state(groups)
    groups.lock_group("red")
    groups.lock_group("green")
    assert state(groups) == before


def test_group_locked_is_a_group_error():
    assert issubclass(GroupLocked, GroupError)


# --- what a lock refuses ----------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda g: g.join("fay", "red"),
        lambda g: g.leave("bob"),
        lambda g: g.swap_students("ann", "cid"),
        lambda g: g.swap_students("cid", "bob"),
        lambda g: g.dissolve_group("red", "blue"),
        lambda g: g.dissolve_group("blue", "red"),
    ],
    ids=[
        "join",
        "leave",
        "swap",
        "swap_neighbours",
        "dissolve_locked",
        "dissolve_into_locked",
    ],
)
def test_a_locked_group_refuses_every_change_of_members(groups, call):
    groups.lock_group("red")
    before = state(groups)
    with pytest.raises(GroupLocked):
        call(groups)
    assert state(groups) == before
    assert groups.get_locked() == ["red"]


def test_dissolving_an_empty_locked_group_is_refused(groups):
    groups.lock_group("green")
    with pytest.raises(GroupLocked):
        groups.dissolve_group("green", "red")
    with pytest.raises(GroupLocked):
        groups.dissolve_group("blue", "green")
    assert groups.get_groups() == ["red", "blue", "green"]
    assert groups.get_members("blue") == ["dan", "eve"]


def test_other_groups_are_not_affected(groups):
    groups.lock_group("red")
    groups.join("fay", "blue")
    groups.leave("dan")
    groups.swap_students("eve", "fay")
    groups.join("gus", "green")
    assert groups.dissolve_group("green", "blue") == 1
    assert state(groups) == [("red", ["ann", "bob", "cid"]), ("blue", ["fay", "eve", "gus"])]


def test_a_locked_group_can_still_be_read_and_groups_added(groups):
    groups.lock_group("red")
    assert groups.get_members("red") == ["ann", "bob", "cid"]
    groups.add_group("pink")
    assert groups.get_groups() == ["red", "blue", "green", "pink"]
    groups.join("fay", "pink")
    assert groups.get_members("pink") == ["fay"]


# --- unlocking --------------------------------------------------------------------


def test_unlock_lets_every_change_through_again(groups):
    groups.lock_group("red")
    groups.unlock_group("red")
    groups.join("fay", "red")
    groups.leave("ann")
    groups.swap_students("bob", "fay")
    assert groups.get_members("red") == ["fay", "cid", "bob"]
    assert groups.dissolve_group("red", "blue") == 3
    assert groups.get_members("blue") == ["dan", "eve", "fay", "cid", "bob"]


def test_an_unlocked_group_works_as_before_after_a_dissolve(groups):
    groups.lock_group("green")
    groups.unlock_group("green")
    groups.dissolve_group("red", "green")
    assert groups.get_locked() == []
    groups.lock_group("blue")
    assert groups.get_locked() == ["blue"]
    groups.leave("ann")
    assert groups.get_members("green") == ["bob", "cid"]
