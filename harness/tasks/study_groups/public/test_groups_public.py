"""Public checks for groups.py.

Usage (with groups.py importable, e.g. in the sandbox):
    python -m pytest public/test_groups_public.py
"""

import pytest
from groups import StudyGroups


@pytest.fixture
def groups():
    g = StudyGroups()
    g.add_group("red")
    g.add_group("blue")
    return g


def test_students_are_listed_in_the_order_they_joined(groups):
    groups.join("cid", "red")
    groups.join("ann", "red")
    groups.join("bob", "red")
    assert groups.get_members("red") == ["cid", "ann", "bob"]
    assert groups.get_members("blue") == []


def test_a_student_who_leaves_is_taken_out(groups):
    for student in ["ann", "bob", "cid"]:
        groups.join(student, "red")
    groups.leave("bob")
    assert groups.get_members("red") == ["ann", "cid"]


def test_groups_are_listed_in_the_order_added(groups):
    groups.add_group("green")
    assert groups.get_groups() == ["red", "blue", "green"]


def test_swap_students_changes_their_positions(groups):
    for student in ["ann", "bob", "cid"]:
        groups.join(student, "red")
    groups.swap_students("ann", "cid")
    assert groups.get_members("red") == ["cid", "bob", "ann"]


def test_dissolve_group_moves_its_members_in_order_and_removes_it(groups):
    groups.join("ann", "red")
    groups.join("bob", "red")
    groups.join("cid", "blue")
    assert groups.dissolve_group("red", "blue") == 2
    assert groups.get_members("blue") == ["cid", "ann", "bob"]
    assert groups.get_groups() == ["blue"]
    with pytest.raises(KeyError):
        groups.get_members("red")
