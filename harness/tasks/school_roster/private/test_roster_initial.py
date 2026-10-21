"""Hidden tests for the initial school_roster spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest private/test_roster_initial.py
"""

import pytest
from roster import Roster, RosterError

BAD_NAMES = ["", None, 7]
BAD_GRADES = [0, 13, -1, 2.5, "3", None]


@pytest.fixture
def roster():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 5)
    ros.add_student("cleo", 3)
    return ros


def state(ros):
    """Every listing, to check that a failed call changed nothing."""
    return (
        [ros.get_students(g) for g in range(1, 13)],
        ros.get_all_students(),
        ros.get_grades(),
    )


# --- adding students --------------------------------------------------------


def test_an_empty_roster_lists_nothing():
    ros = Roster()
    assert ros.get_all_students() == []
    assert ros.get_grades() == []
    assert ros.get_students(1) == []


def test_added_students_are_in_their_grade(roster):
    roster.add_student("dev", 12)
    assert roster.get_grade("dev") == 12
    assert roster.get_grade("cleo") == 3
    assert roster.get_students(12) == ["dev"]


def test_grades_one_and_twelve_are_allowed():
    ros = Roster()
    ros.add_student("ana", 1)
    ros.add_student("ben", 12)
    assert ros.get_grades() == [1, 12]


@pytest.mark.parametrize("name", BAD_NAMES)
def test_invalid_names_are_rejected(roster, name):
    before = state(roster)
    with pytest.raises(ValueError):
        roster.add_student(name, 4)
    assert state(roster) == before


@pytest.mark.parametrize("grade", BAD_GRADES)
def test_invalid_grades_are_rejected_when_adding(roster, grade):
    before = state(roster)
    with pytest.raises(ValueError):
        roster.add_student("dev", grade)
    assert state(roster) == before
    with pytest.raises(KeyError):
        roster.get_grade("dev")


@pytest.mark.parametrize("grade", [3, 8])
def test_a_name_already_on_the_roster_is_rejected(roster, grade):
    before = state(roster)
    with pytest.raises(RosterError):
        roster.add_student("ana", grade)
    assert state(roster) == before
    assert roster.get_grade("ana") == 3


def test_a_bad_grade_is_reported_before_a_repeated_name(roster):
    with pytest.raises(ValueError):
        roster.add_student("ana", 0)
    with pytest.raises(ValueError):
        roster.add_student("ana", "3")


def test_a_bad_name_is_reported_before_a_bad_grade(roster):
    with pytest.raises(ValueError):
        roster.add_student("", 99)


# --- looking up students ----------------------------------------------------


@pytest.mark.parametrize("name", ["zed", "", None, 7])
def test_names_not_on_the_roster_raise_key_error(roster, name):
    with pytest.raises(KeyError):
        roster.get_grade(name)


def test_students_of_a_grade_keep_their_arrival_order(roster):
    roster.add_student("dev", 3)
    roster.add_student("eli", 5)
    assert roster.get_students(3) == ["ana", "cleo", "dev"]
    assert roster.get_students(5) == ["ben", "eli"]


def test_a_grade_with_no_students_gives_an_empty_list(roster):
    assert roster.get_students(1) == []
    assert roster.get_students(12) == []


@pytest.mark.parametrize("grade", BAD_GRADES)
def test_invalid_grades_are_rejected_when_listing(roster, grade):
    with pytest.raises(ValueError):
        roster.get_students(grade)


def test_all_students_are_sorted_by_grade_lowest_first(roster):
    roster.add_student("dev", 1)
    roster.add_student("eli", 12)
    roster.add_student("fay", 5)
    assert roster.get_all_students() == ["dev", "ana", "cleo", "ben", "fay", "eli"]


def test_students_in_the_same_grade_stay_in_arrival_order_not_alphabetical():
    ros = Roster()
    ros.add_student("zed", 2)
    ros.add_student("amy", 2)
    ros.add_student("mo", 2)
    assert ros.get_students(2) == ["zed", "amy", "mo"]
    assert ros.get_all_students() == ["zed", "amy", "mo"]


def test_grades_are_listed_once_each_lowest_first():
    ros = Roster()
    ros.add_student("ana", 9)
    ros.add_student("ben", 2)
    ros.add_student("cleo", 9)
    ros.add_student("dev", 11)
    assert ros.get_grades() == [2, 9, 11]


def test_names_may_look_like_numbers():
    ros = Roster()
    ros.add_student("7", 7)
    assert ros.get_grade("7") == 7
    assert ros.get_students(7) == ["7"]
    with pytest.raises(KeyError):
        ros.get_grade(7)


def test_rosters_do_not_share_students():
    first, second = Roster(), Roster()
    first.add_student("ana", 3)
    assert second.get_all_students() == []
    second.add_student("ana", 4)
    assert first.get_grade("ana") == 3
    assert second.get_grade("ana") == 4
