"""Hidden tests for the c_move change (moving students, grade caps). Never
shown to the writer or the editor.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move/private/test_move_new.py
"""

import pytest
from roster import GradeFull, Roster, RosterError

BAD_CAPS = [0, -1, 2.5, "3", True]


@pytest.fixture
def roster():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 5)
    ros.add_student("cleo", 3)
    ros.add_student("dev", 5)
    return ros


@pytest.fixture
def capped():
    ros = Roster(cap=2)
    ros.add_student("ana", 1)
    ros.add_student("ben", 1)
    ros.add_student("cleo", 2)
    ros.add_student("dev", 3)
    return ros


def state(ros):
    return (
        [ros.get_students(g) for g in range(1, 13)],
        ros.get_all_students(),
        ros.get_grades(),
    )


# --- moving -----------------------------------------------------------------


def test_a_moved_student_changes_grade(roster):
    roster.move_students(["ana"], 5)
    assert roster.get_grade("ana") == 5
    assert roster.get_students(3) == ["cleo"]
    assert roster.get_students(5) == ["ben", "dev", "ana"]
    assert roster.get_grades() == [3, 5]


def test_moved_students_arrive_in_the_order_listed(roster):
    roster.move_students(["dev", "ana"], 7)
    assert roster.get_students(7) == ["dev", "ana"]
    assert roster.get_all_students() == ["cleo", "ben", "dev", "ana"]
    assert roster.get_grades() == [3, 5, 7]


def test_all_students_follows_the_new_grade_order(roster):
    roster.move_students(["ben"], 1)
    roster.move_students(["cleo"], 5)
    assert roster.get_all_students() == ["ben", "ana", "dev", "cleo"]


def test_a_student_already_in_the_grade_keeps_their_place(roster):
    roster.move_students(["ana", "ben"], 3)
    assert roster.get_students(3) == ["ana", "cleo", "ben"]
    roster.move_students(["cleo"], 3)
    assert roster.get_students(3) == ["ana", "cleo", "ben"]


def test_an_empty_list_changes_nothing(roster):
    before = state(roster)
    roster.move_students([], 9)
    assert state(roster) == before


def test_a_grade_emptied_by_a_move_disappears_from_grades(roster):
    roster.move_students(["ana", "cleo"], 5)
    assert roster.get_students(3) == []
    assert roster.get_grades() == [5]


def test_moving_back_puts_the_student_at_the_end(roster):
    roster.move_students(["ana"], 5)
    roster.move_students(["ana"], 3)
    assert roster.get_students(3) == ["cleo", "ana"]


# --- failed moves -----------------------------------------------------------


@pytest.mark.parametrize("grade", [0, 13, 2.5, "3", None])
def test_an_invalid_grade_moves_nobody(roster, grade):
    before = state(roster)
    with pytest.raises(ValueError):
        roster.move_students(["ana"], grade)
    assert state(roster) == before


@pytest.mark.parametrize("names", [["zed"], ["ana", "zed"], ["ana", None, "ben"]])
def test_an_unknown_name_moves_nobody(roster, names):
    before = state(roster)
    with pytest.raises(KeyError):
        roster.move_students(names, 7)
    assert state(roster) == before


def test_a_name_listed_twice_moves_nobody(roster):
    before = state(roster)
    with pytest.raises(ValueError):
        roster.move_students(["ana", "ben", "ana"], 7)
    assert state(roster) == before


def test_an_invalid_grade_is_reported_before_an_unknown_name(roster):
    with pytest.raises(ValueError):
        roster.move_students(["zed"], 0)


def test_an_unknown_name_is_reported_before_a_repeated_name(roster):
    with pytest.raises(KeyError):
        roster.move_students(["ana", "ana", "zed"], 7)


# --- caps -------------------------------------------------------------------


def test_no_cap_means_no_limit():
    ros = Roster()
    assert ros.get_cap() is None
    for i in range(40):
        ros.add_student(f"s{i}", 6)
    ros.move_students([f"s{i}" for i in range(40)], 7)
    assert len(ros.get_students(7)) == 40


@pytest.mark.parametrize("cap", BAD_CAPS)
def test_invalid_caps_are_rejected(cap):
    with pytest.raises(ValueError):
        Roster(cap=cap)


def test_a_cap_of_one_works():
    ros = Roster(cap=1)
    ros.add_student("ana", 1)
    with pytest.raises(GradeFull):
        ros.add_student("ben", 1)
    ros.add_student("ben", 2)
    assert ros.get_students(1) == ["ana"]


def test_adding_to_a_full_grade_changes_nothing(capped):
    before = state(capped)
    with pytest.raises(GradeFull):
        capped.add_student("eli", 1)
    assert state(capped) == before
    with pytest.raises(KeyError):
        capped.get_grade("eli")


def test_a_move_past_the_cap_moves_nobody(capped):
    before = state(capped)
    with pytest.raises(GradeFull):
        capped.move_students(["ana", "dev"], 2)
    assert state(capped) == before
    with pytest.raises(GradeFull):
        capped.move_students(["dev"], 1)
    assert state(capped) == before


def test_a_move_that_exactly_fills_the_grade_works(capped):
    capped.move_students(["dev"], 2)
    assert capped.get_students(2) == ["cleo", "dev"]
    capped.move_students(["ana", "ben"], 3)
    assert capped.get_students(3) == ["ana", "ben"]
    assert capped.get_students(1) == []


def test_students_already_in_the_grade_do_not_count_as_arriving(capped):
    capped.move_students(["ana", "ben"], 1)
    assert capped.get_students(1) == ["ana", "ben"]
    capped.move_students(["cleo", "dev"], 2)
    assert capped.get_students(2) == ["cleo", "dev"]


def test_grade_full_is_a_roster_error():
    assert issubclass(GradeFull, RosterError)


def test_a_repeated_name_is_reported_before_a_full_grade(capped):
    with pytest.raises(ValueError):
        capped.move_students(["dev", "dev"], 1)
    with pytest.raises(RosterError) as caught:
        capped.add_student("ana", 1)  # already on the roster, before the cap
    assert not isinstance(caught.value, GradeFull)
