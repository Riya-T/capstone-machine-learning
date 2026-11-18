"""Hidden tests for the c_find change (finding students). Never shown to the
writer or the editor. They call only the spec's methods and this change's
own, never undo.

Usage (with groups.py importable, e.g. in the sandbox):
    python -m pytest changes/c_find/private/test_find_new.py
"""

import pytest
from groups import StudyGroups


@pytest.fixture
def groups():
    g = StudyGroups()
    for name in ["red", "blue", "green"]:
        g.add_group(name)
    for student in ["cid", "ann", "bob"]:
        g.join(student, "red")
    g.join("eve", "blue")
    g.join("dan", "blue")
    return g


def state(g):
    return [(name, g.get_members(name)) for name in g.get_groups()]


# --- find_student -------------------------------------------------------------------


def test_positions_count_from_1_in_join_order(groups):
    assert groups.find_student("cid") == ("red", 1)
    assert groups.find_student("ann") == ("red", 2)
    assert groups.find_student("bob") == ("red", 3)
    assert groups.find_student("eve") == ("blue", 1)
    assert groups.find_student("dan") == ("blue", 2)


def test_find_student_returns_a_tuple(groups):
    result = groups.find_student("bob")
    assert isinstance(result, tuple)
    group, position = result
    assert (group, position) == ("red", 3)


def test_a_student_in_no_group_raises_key_error(groups):
    with pytest.raises(KeyError):
        groups.find_student("zoe")
    groups.leave("ann")
    with pytest.raises(KeyError):
        groups.find_student("ann")


def test_positions_close_up_after_a_leave(groups):
    groups.leave("cid")
    assert groups.find_student("ann") == ("red", 1)
    assert groups.find_student("bob") == ("red", 2)


def test_a_student_who_joins_again_is_found_in_the_new_group(groups):
    groups.leave("cid")
    groups.join("cid", "green")
    assert groups.find_student("cid") == ("green", 1)
    groups.join("fay", "blue")
    assert groups.find_student("fay") == ("blue", 3)


def test_find_student_after_a_swap_in_the_second_group(groups):
    groups.swap_students("eve", "dan")
    assert groups.find_student("dan") == ("blue", 1)
    assert groups.find_student("eve") == ("blue", 2)


def test_find_student_after_a_swap_in_the_same_group(groups):
    groups.swap_students("cid", "bob")
    assert groups.find_student("bob") == ("red", 1)
    assert groups.find_student("cid") == ("red", 3)
    assert groups.find_student("ann") == ("red", 2)


def test_find_student_after_a_dissolve(groups):
    groups.dissolve_group("red", "blue")
    assert groups.find_student("eve") == ("blue", 1)
    assert groups.find_student("cid") == ("blue", 3)
    assert groups.find_student("bob") == ("blue", 5)


# --- get_students -------------------------------------------------------------------


def test_get_students_follows_group_order_then_member_order(groups):
    assert groups.get_students() == ["cid", "ann", "bob", "eve", "dan"]


def test_empty_groups_add_nobody(groups):
    groups.join("fay", "green")
    groups.leave("eve")
    groups.leave("dan")
    assert groups.get_students() == ["cid", "ann", "bob", "fay"]


def test_get_students_with_no_students():
    g = StudyGroups()
    g.add_group("red")
    assert g.get_students() == []


def test_get_students_after_a_swap_and_a_dissolve(groups):
    groups.swap_students("ann", "bob")
    assert groups.get_students() == ["cid", "bob", "ann", "eve", "dan"]
    groups.dissolve_group("red", "green")
    assert groups.get_students() == ["eve", "dan", "cid", "bob", "ann"]


def test_get_students_follows_the_order_groups_were_added():
    g = StudyGroups()
    for name in ["zeta", "alpha"]:
        g.add_group(name)
    g.join("yan", "alpha")
    g.join("xia", "zeta")
    assert g.get_students() == ["xia", "yan"]


# --- nothing changes --------------------------------------------------------------


def test_finding_changes_nothing(groups):
    before = state(groups)
    groups.find_student("ann")
    groups.get_students()
    with pytest.raises(KeyError):
        groups.find_student("zoe")
    assert state(groups) == before
    groups.join("zoe", "green")
    assert groups.find_student("zoe") == ("green", 1)
