"""Public checks for roster.py.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest public/test_roster_public.py
"""

import pytest
from roster import Roster


@pytest.fixture
def roster():
    ros = Roster()
    ros.add_student("ana", 3)
    ros.add_student("ben", 5)
    ros.add_student("cleo", 3)
    return ros


def test_a_student_is_in_the_grade_given(roster):
    assert roster.get_grade("ana") == 3
    assert roster.get_grade("ben") == 5


def test_students_of_a_grade_are_listed_in_the_order_added(roster):
    assert roster.get_students(3) == ["ana", "cleo"]
    assert roster.get_students(5) == ["ben"]


def test_a_grade_without_students_gives_an_empty_list(roster):
    assert roster.get_students(7) == []


def test_all_students_are_ordered_by_grade_then_by_arrival(roster):
    roster.add_student("dev", 1)
    assert roster.get_all_students() == ["dev", "ana", "cleo", "ben"]
    assert roster.get_grades() == [1, 3, 5]


def test_an_unknown_name_raises_key_error(roster):
    with pytest.raises(KeyError):
        roster.get_grade("zed")


def test_grade_zero_is_rejected(roster):
    with pytest.raises(ValueError):
        roster.add_student("eli", 0)
    with pytest.raises(ValueError):
        roster.get_students(0)
