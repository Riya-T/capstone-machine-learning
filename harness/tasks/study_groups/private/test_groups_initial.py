"""Hidden tests for the initial study_groups spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with groups.py importable, e.g. in the sandbox):
    python -m pytest private/test_groups_initial.py
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
    """Every group in order with its members, to check that a failed call
    changed nothing."""
    return [(name, g.get_members(name)) for name in g.get_groups()]


# --- groups -------------------------------------------------------------------


def test_a_new_group_is_empty():
    g = StudyGroups()
    g.add_group("red")
    assert g.get_members("red") == []


def test_groups_are_listed_in_the_order_added():
    g = StudyGroups()
    for name in ["blue", "red", "green"]:
        g.add_group(name)
    assert g.get_groups() == ["blue", "red", "green"]


def test_a_new_instance_has_no_groups():
    assert StudyGroups().get_groups() == []


def test_adding_a_name_in_use_is_rejected(groups):
    before = state(groups)
    with pytest.raises(GroupError):
        groups.add_group("red")
    assert state(groups) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda g: g.join("zoe", "pink"),
        lambda g: g.dissolve_group("pink", "red"),
        lambda g: g.dissolve_group("red", "pink"),
        lambda g: g.get_members("pink"),
    ],
)
def test_groups_that_were_never_added_raise_key_error(groups, call):
    before = state(groups)
    with pytest.raises(KeyError):
        call(groups)
    assert state(groups) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda g: g.join("zoe", "green"),
        lambda g: g.dissolve_group("green", "red"),
        lambda g: g.dissolve_group("red", "green"),
        lambda g: g.get_members("green"),
    ],
)
def test_a_dissolved_group_is_not_in_use(groups, call):
    groups.dissolve_group("green", "blue")  # green is empty
    before = state(groups)
    with pytest.raises(KeyError):
        call(groups)
    assert state(groups) == before


# --- joining and leaving --------------------------------------------------------


def test_join_adds_students_at_the_end(groups):
    groups.join("fay", "blue")
    groups.join("gus", "green")
    assert groups.get_members("blue") == ["dan", "eve", "fay"]
    assert groups.get_members("green") == ["gus"]
    assert groups.get_members("red") == ["ann", "bob", "cid"]


def test_leave_keeps_the_others_in_order(groups):
    groups.leave("ann")
    assert groups.get_members("red") == ["bob", "cid"]
    groups.leave("cid")
    assert groups.get_members("red") == ["bob"]


def test_leave_finds_the_student_in_any_group(groups):
    groups.leave("eve")
    assert groups.get_members("blue") == ["dan"]
    assert groups.get_members("red") == ["ann", "bob", "cid"]


def test_leaving_without_a_group_raises_key_error(groups):
    groups.leave("eve")
    before = state(groups)
    with pytest.raises(KeyError):
        groups.leave("eve")
    with pytest.raises(KeyError):
        groups.leave("zoe")
    assert state(groups) == before


# --- swapping -------------------------------------------------------------------


def test_swap_students_changes_their_positions(groups):
    groups.swap_students("ann", "cid")
    assert groups.get_members("red") == ["cid", "bob", "ann"]
    groups.swap_students("bob", "cid")
    assert groups.get_members("red") == ["bob", "cid", "ann"]
    groups.swap_students("eve", "dan")
    assert groups.get_members("blue") == ["eve", "dan"]


def test_swapped_students_keep_their_new_positions(groups):
    groups.swap_students("ann", "cid")
    groups.leave("ann")
    assert groups.get_members("red") == ["cid", "bob"]
    groups.join("fay", "red")
    groups.swap_students("fay", "cid")
    assert groups.get_members("red") == ["fay", "bob", "cid"]


def test_swapping_a_student_with_themselves_is_rejected(groups):
    before = state(groups)
    with pytest.raises(ValueError):
        groups.swap_students("bob", "bob")
    assert state(groups) == before


@pytest.mark.parametrize(
    "a, b", [("zoe", "ann"), ("ann", "zoe"), ("zoe", "yan")], ids=["first", "second", "both"]
)
def test_swapping_a_student_without_a_group_raises_key_error(groups, a, b):
    before = state(groups)
    with pytest.raises(KeyError):
        groups.swap_students(a, b)
    assert state(groups) == before


# --- dissolving -------------------------------------------------------------------


def test_dissolve_group_appends_the_members_in_order(groups):
    assert groups.dissolve_group("red", "blue") == 3
    assert groups.get_members("blue") == ["dan", "eve", "ann", "bob", "cid"]
    assert groups.get_groups() == ["blue", "green"]


def test_dissolving_into_an_empty_group(groups):
    assert groups.dissolve_group("blue", "green") == 2
    assert groups.get_members("green") == ["dan", "eve"]
    assert groups.get_groups() == ["red", "green"]


def test_dissolving_an_empty_group_moves_nothing(groups):
    assert groups.dissolve_group("green", "red") == 0
    assert groups.get_groups() == ["red", "blue"]
    assert groups.get_members("red") == ["ann", "bob", "cid"]


def test_the_other_groups_keep_their_order_after_a_dissolve(groups):
    groups.add_group("pink")
    groups.dissolve_group("blue", "pink")
    assert groups.get_groups() == ["red", "green", "pink"]


def test_moved_students_belong_to_the_group_they_were_moved_into(groups):
    groups.dissolve_group("blue", "red")
    groups.leave("dan")
    assert groups.get_members("red") == ["ann", "bob", "cid", "eve"]
    groups.swap_students("eve", "ann")
    assert groups.get_members("red") == ["eve", "bob", "cid", "ann"]


def test_dissolving_a_group_into_itself_is_rejected(groups):
    before = state(groups)
    with pytest.raises(ValueError):
        groups.dissolve_group("red", "red")
    with pytest.raises(ValueError):
        groups.dissolve_group("green", "green")
    assert state(groups) == before


# --- general ----------------------------------------------------------------------


def test_instances_do_not_share_groups():
    first, second = StudyGroups(), StudyGroups()
    first.add_group("red")
    first.join("ann", "red")
    assert second.get_groups() == []
    second.add_group("red")
    second.join("ann", "red")
    assert second.get_members("red") == ["ann"]
