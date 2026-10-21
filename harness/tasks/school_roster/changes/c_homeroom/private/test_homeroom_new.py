"""Hidden tests for the c_homeroom change (homerooms). Never shown to the
writer or the editor.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_homeroom/private/test_homeroom_new.py
"""

import pytest
from roster import Roster, RosterError

BAD_ROOMS = ["", None, 3]


@pytest.fixture
def roster():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 3)
    ros.add_student("cleo", 3)
    ros.add_student("dev", 5)
    ros.assign_homeroom("ana", "east")
    ros.assign_homeroom("ben", "east")
    ros.assign_homeroom("dev", "west")
    return ros


def state(ros):
    return (
        [ros.get_students(g) for g in range(1, 13)],
        {n: ros.get_homeroom(n) for n in ros.get_all_students()},
        {r: ros.get_homeroom_students(r) for r in ros.get_homerooms()},
        ros.get_homerooms(),
    )


# --- assigning --------------------------------------------------------------


def test_new_students_have_no_homeroom(roster):
    assert roster.get_homeroom("cleo") is None
    roster.add_student("eli", 3)
    assert roster.get_homeroom("eli") is None


def test_students_join_a_room_in_assignment_order(roster):
    roster.assign_homeroom("cleo", "east")
    assert roster.get_homeroom_students("east") == ["ana", "ben", "cleo"]
    assert roster.get_homeroom_students("west") == ["dev"]


def test_reassigning_moves_the_student_to_the_end_of_the_new_room(roster):
    roster.assign_homeroom("cleo", "north")
    roster.assign_homeroom("ana", "north")
    assert roster.get_homeroom("ana") == "north"
    assert roster.get_homeroom_students("east") == ["ben"]
    assert roster.get_homeroom_students("north") == ["cleo", "ana"]


def test_assigning_the_current_room_changes_nothing(roster):
    before = state(roster)
    roster.assign_homeroom("ana", "east")
    assert state(roster) == before
    assert roster.get_homeroom_students("east") == ["ana", "ben"]


def test_an_unused_room_has_no_students(roster):
    assert roster.get_homeroom_students("south") == []


def test_rooms_are_listed_in_the_order_first_used(roster):
    roster.assign_homeroom("cleo", "north")
    assert roster.get_homerooms() == ["east", "west", "north"]


def test_an_emptied_room_is_not_listed_but_keeps_its_place(roster):
    roster.assign_homeroom("dev", "south")
    assert roster.get_homerooms() == ["east", "south"]
    assert roster.get_homeroom_students("west") == []
    roster.assign_homeroom("dev", "west")
    assert roster.get_homerooms() == ["east", "west"]


# --- one grade per room -----------------------------------------------------


def test_a_student_of_another_grade_is_refused(roster):
    before = state(roster)
    with pytest.raises(RosterError):
        roster.assign_homeroom("dev", "east")
    with pytest.raises(RosterError):
        roster.assign_homeroom("cleo", "west")
    assert state(roster) == before


def test_an_emptied_room_can_take_another_grade(roster):
    roster.assign_homeroom("dev", "south")
    roster.assign_homeroom("cleo", "west")
    assert roster.get_homeroom_students("west") == ["cleo"]


# --- errors -----------------------------------------------------------------


@pytest.mark.parametrize("name", ["zed", None, 7])
def test_names_not_on_the_roster_raise_key_error(roster, name):
    with pytest.raises(KeyError):
        roster.assign_homeroom(name, "east")
    with pytest.raises(KeyError):
        roster.get_homeroom(name)
    assert roster.get_homeroom_students("east") == ["ana", "ben"]


@pytest.mark.parametrize("room", BAD_ROOMS)
def test_invalid_rooms_are_rejected(roster, room):
    before = state(roster)
    with pytest.raises(ValueError):
        roster.assign_homeroom("cleo", room)
    with pytest.raises(ValueError):
        roster.get_homeroom_students(room)
    assert state(roster) == before


def test_an_unknown_name_is_reported_before_a_bad_room(roster):
    with pytest.raises(KeyError):
        roster.assign_homeroom("zed", "")


def test_a_bad_room_is_reported_before_a_grade_mismatch(roster):
    with pytest.raises(ValueError):
        roster.assign_homeroom("dev", None)


# --- moving grades ----------------------------------------------------------


def test_a_moved_student_leaves_their_homeroom(roster):
    roster.move_students(["ana", "dev"], 7)
    assert roster.get_homeroom("ana") is None
    assert roster.get_homeroom("dev") is None
    assert roster.get_homeroom_students("east") == ["ben"]
    assert roster.get_homerooms() == ["east"]


def test_a_student_moved_within_their_grade_keeps_their_homeroom(roster):
    roster.move_students(["ana", "cleo"], 3)
    assert roster.get_homeroom("ana") == "east"
    assert roster.get_homeroom_students("east") == ["ana", "ben"]


def test_a_failed_move_changes_no_homerooms(roster):
    before = state(roster)
    with pytest.raises(KeyError):
        roster.move_students(["ana", "zed"], 7)
    with pytest.raises(ValueError):
        roster.move_students(["ana", "ana"], 7)
    assert state(roster) == before


def test_a_moved_student_can_join_a_room_of_the_new_grade(roster):
    roster.move_students(["ana"], 5)
    roster.assign_homeroom("ana", "west")
    assert roster.get_homeroom_students("west") == ["dev", "ana"]
