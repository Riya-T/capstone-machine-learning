"""Hidden tests for the c_withdraw change (withdrawing and reinstating
students). Never shown to the writer or the editor.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_withdraw/private/test_withdraw_new.py
"""

import pytest
from roster import Roster, RosterError


@pytest.fixture
def roster():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 5)
    ros.add_student("cleo", 3)
    return ros


def state(ros):
    return (
        [ros.get_students(g) for g in range(1, 13)],
        ros.get_all_students(),
        ros.get_grades(),
        ros.get_withdrawn(),
    )


# --- withdrawing ------------------------------------------------------------


def test_nobody_is_withdrawn_at_first(roster):
    assert roster.get_withdrawn() == []


def test_a_withdrawn_student_is_in_no_listing(roster):
    roster.withdraw_student("ana")
    assert roster.get_students(3) == ["cleo"]
    assert roster.get_all_students() == ["cleo", "ben"]
    with pytest.raises(KeyError):
        roster.get_grade("ana")


def test_withdrawing_the_last_student_of_a_grade_drops_the_grade(roster):
    roster.withdraw_student("ben")
    assert roster.get_grades() == [3]
    assert roster.get_students(5) == []


def test_withdrawn_names_are_listed_in_withdrawal_order(roster):
    roster.withdraw_student("cleo")
    roster.withdraw_student("ana")
    assert roster.get_withdrawn() == ["cleo", "ana"]
    assert roster.get_all_students() == ["ben"]


@pytest.mark.parametrize("name", ["zed", None, 7])
def test_withdrawing_a_name_not_on_the_roster_raises(roster, name):
    before = state(roster)
    with pytest.raises(KeyError):
        roster.withdraw_student(name)
    assert state(roster) == before


def test_withdrawing_an_already_withdrawn_student_raises(roster):
    roster.withdraw_student("ana")
    before = state(roster)
    with pytest.raises(KeyError):
        roster.withdraw_student("ana")
    assert state(roster) == before


# --- reinstating ------------------------------------------------------------


def test_a_reinstated_student_rejoins_their_old_grade_at_the_end(roster):
    roster.withdraw_student("ana")
    roster.add_student("dev", 3)
    roster.reinstate_student("ana")
    assert roster.get_grade("ana") == 3
    assert roster.get_students(3) == ["cleo", "dev", "ana"]
    assert roster.get_all_students() == ["cleo", "dev", "ana", "ben"]
    assert roster.get_withdrawn() == []


def test_reinstating_restores_an_emptied_grade(roster):
    roster.withdraw_student("ben")
    roster.reinstate_student("ben")
    assert roster.get_grades() == [3, 5]
    assert roster.get_students(5) == ["ben"]


def test_reinstating_one_of_several_leaves_the_others_withdrawn(roster):
    roster.withdraw_student("ana")
    roster.withdraw_student("ben")
    roster.withdraw_student("cleo")
    roster.reinstate_student("ben")
    assert roster.get_withdrawn() == ["ana", "cleo"]
    assert roster.get_all_students() == ["ben"]


@pytest.mark.parametrize("name", ["zed", "ana", None])
def test_reinstating_a_name_that_is_not_withdrawn_raises(roster, name):
    before = state(roster)
    with pytest.raises(KeyError):
        roster.reinstate_student(name)
    assert state(roster) == before


def test_a_student_can_be_withdrawn_and_reinstated_repeatedly(roster):
    roster.withdraw_student("ana")
    roster.reinstate_student("ana")
    roster.withdraw_student("ana")
    assert roster.get_withdrawn() == ["ana"]
    assert roster.get_students(3) == ["cleo"]
    roster.reinstate_student("ana")
    assert roster.get_students(3) == ["cleo", "ana"]


# --- adding a withdrawn name again -----------------------------------------


def test_adding_a_withdrawn_name_starts_the_student_afresh(roster):
    roster.withdraw_student("ana")
    roster.add_student("ana", 9)
    assert roster.get_grade("ana") == 9
    assert roster.get_students(3) == ["cleo"]
    assert roster.get_students(9) == ["ana"]
    assert roster.get_withdrawn() == []


def test_a_readded_student_cannot_be_reinstated(roster):
    roster.withdraw_student("ana")
    roster.add_student("ana", 3)
    with pytest.raises(KeyError):
        roster.reinstate_student("ana")
    assert roster.get_students(3) == ["cleo", "ana"]


def test_adding_a_withdrawn_name_with_a_bad_grade_keeps_it_withdrawn(roster):
    roster.withdraw_student("ana")
    before = state(roster)
    with pytest.raises(ValueError):
        roster.add_student("ana", 13)
    assert state(roster) == before
    assert roster.get_withdrawn() == ["ana"]


def test_a_withdrawn_name_is_not_a_repeated_name(roster):
    roster.withdraw_student("ana")
    try:
        roster.add_student("ana", 3)
    except RosterError:
        pytest.fail("a withdrawn name may be added again")
