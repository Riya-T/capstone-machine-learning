"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor. They call only the spec's methods and undo, since they run in
both sequences.

Usage (with groups.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from groups import GroupError, StudyGroups


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


# --- each call can be undone ----------------------------------------------------


def test_undo_of_a_join(groups):
    before = state(groups)
    groups.join("fay", "green")
    groups.undo()
    assert state(groups) == before
    groups.join("fay", "red")
    assert groups.get_members("red") == ["ann", "bob", "cid", "fay"]


def test_undo_of_a_leave_puts_the_student_back_in_place(groups):
    before = state(groups)
    groups.leave("bob")
    groups.undo()
    assert state(groups) == before
    assert groups.get_members("red") == ["ann", "bob", "cid"]


def test_a_student_put_back_by_undo_is_in_the_group_again(groups):
    groups.leave("ann")
    groups.undo()
    groups.swap_students("ann", "cid")
    assert groups.get_members("red") == ["cid", "bob", "ann"]
    groups.leave("ann")
    assert groups.get_members("red") == ["cid", "bob"]


def test_undo_of_a_swap_of_neighbours(groups):
    before = state(groups)
    groups.swap_students("cid", "bob")
    groups.undo()
    assert state(groups) == before


def test_undo_of_a_swap_in_the_same_group(groups):
    before = state(groups)
    groups.swap_students("ann", "cid")
    groups.undo()
    assert state(groups) == before


def test_one_undo_takes_back_a_whole_dissolve(groups):
    before = state(groups)
    assert groups.dissolve_group("red", "blue") == 3
    groups.undo()
    assert state(groups) == before
    assert groups.get_groups() == ["red", "blue", "green"]
    assert groups.get_members("blue") == ["dan", "eve"]


def test_undo_of_a_dissolve_puts_the_group_back_at_its_place(groups):
    groups.add_group("pink")
    before = state(groups)
    groups.dissolve_group("blue", "pink")
    assert groups.get_groups() == ["red", "green", "pink"]
    groups.undo()
    assert groups.get_groups() == ["red", "blue", "green", "pink"]
    assert state(groups) == before


def test_a_group_brought_back_is_in_use_again(groups):
    groups.dissolve_group("red", "green")
    groups.undo()
    groups.join("fay", "red")
    assert groups.get_members("red") == ["ann", "bob", "cid", "fay"]
    assert groups.get_members("green") == []
    with pytest.raises(GroupError):
        groups.add_group("red")
    assert groups.dissolve_group("red", "blue") == 4
    assert groups.get_groups() == ["blue", "green"]


def test_undo_of_add_group_removes_it_and_frees_the_name(groups):
    groups.add_group("pink")
    groups.undo()
    assert groups.get_groups() == ["red", "blue", "green"]
    with pytest.raises(KeyError):
        groups.get_members("pink")
    groups.add_group("pink")
    assert groups.get_groups() == ["red", "blue", "green", "pink"]
    assert groups.get_members("pink") == []


def test_undoing_two_dissolves_in_a_row_restores_the_order(groups):
    before = state(groups)
    groups.dissolve_group("red", "green")
    groups.dissolve_group("blue", "green")
    assert groups.get_members("green") == ["ann", "bob", "cid", "dan", "eve"]
    groups.undo()
    assert state(groups) == [("blue", ["dan", "eve"]), ("green", ["ann", "bob", "cid"])]
    groups.undo()
    assert state(groups) == before


def test_undo_after_a_leave_and_a_swap(groups):
    before = state(groups)
    groups.leave("ann")
    groups.swap_students("bob", "cid")
    assert state(groups)[:2] == [("red", ["cid", "bob"]), ("blue", ["dan", "eve"])]
    groups.undo()
    assert groups.get_members("red") == ["bob", "cid"]
    groups.undo()
    assert state(groups) == before


# --- calls that move nothing ----------------------------------------------------


def test_dissolving_an_empty_group_can_be_undone(groups):
    groups.join("fay", "blue")
    assert groups.dissolve_group("green", "blue") == 0
    groups.undo()
    assert groups.get_groups() == ["red", "blue", "green"]
    assert groups.get_members("blue") == ["dan", "eve", "fay"]
    groups.undo()
    assert groups.get_members("blue") == ["dan", "eve"]


# --- what is and is not recorded --------------------------------------------------


def test_each_undo_goes_one_call_further_back():
    g = StudyGroups()
    calls = [
        lambda: g.add_group("red"),
        lambda: g.add_group("blue"),
        lambda: g.join("ann", "red"),
        lambda: g.join("bob", "red"),
        lambda: g.join("cid", "blue"),
        lambda: g.add_group("green"),
        lambda: g.join("dan", "red"),
        lambda: g.swap_students("ann", "dan"),
        lambda: g.leave("bob"),
        lambda: g.join("bob", "green"),
        lambda: g.dissolve_group("red", "blue"),
        lambda: g.swap_students("cid", "ann"),
        lambda: g.add_group("pink"),
        lambda: g.dissolve_group("green", "pink"),
    ]
    states = [state(g)]
    for call in calls:
        call()
        states.append(state(g))
    assert state(g) == [("blue", ["ann", "dan", "cid"]), ("pink", ["bob"])]
    for expected in reversed(states[:-1]):
        g.undo()
        assert state(g) == expected
    with pytest.raises(GroupError):
        g.undo()
    assert g.get_groups() == []


def test_failed_calls_are_not_recorded(groups):
    groups.join("fay", "green")
    for call in (
        lambda: groups.add_group("red"),
        lambda: groups.join("zoe", "pink"),
        lambda: groups.leave("zoe"),
        lambda: groups.swap_students("ann", "ann"),
        lambda: groups.swap_students("ann", "zoe"),
        lambda: groups.dissolve_group("red", "red"),
        lambda: groups.dissolve_group("pink", "red"),
    ):
        with pytest.raises((ValueError, KeyError, GroupError)):
            call()
    groups.undo()  # fay joining green
    assert groups.get_members("green") == []
    assert groups.get_members("red") == ["ann", "bob", "cid"]


def test_get_calls_are_not_recorded(groups):
    groups.join("fay", "green")
    groups.get_members("green")
    groups.get_groups()
    groups.undo()
    assert groups.get_members("green") == []
    assert groups.get_members("blue") == ["dan", "eve"]


def test_there_is_no_redo():
    g = StudyGroups()
    g.add_group("red")
    g.join("ann", "red")
    g.undo()
    g.undo()
    assert g.get_groups() == []
    with pytest.raises(GroupError):
        g.undo()


def test_new_calls_after_an_undo_are_undone_first(groups):
    groups.join("fay", "green")
    groups.undo()
    groups.join("gus", "green")
    groups.undo()
    assert groups.get_members("green") == []
    groups.undo()  # eve joining blue in the fixture
    assert groups.get_members("blue") == ["dan"]
    assert groups.get_members("red") == ["ann", "bob", "cid"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    g = StudyGroups()
    with pytest.raises(GroupError):
        g.undo()
    g.add_group("red")
    g.undo()
    with pytest.raises(GroupError):
        g.undo()
    assert g.get_groups() == []
    g.add_group("red")
    g.join("ann", "red")
    assert g.get_members("red") == ["ann"]


def test_the_whole_fixture_can_be_undone(groups):
    for _ in range(8):
        groups.undo()
    assert groups.get_groups() == []
    with pytest.raises(GroupError):
        groups.undo()
