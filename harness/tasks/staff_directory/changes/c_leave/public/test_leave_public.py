"""Public checks for the c_leave change (employees on leave). Shown to the
editor, never to the writer.

Usage (with directory.py importable, e.g. in the sandbox):
    python -m pytest changes/c_leave/public/test_leave_public.py
"""

import pytest
from directory import Directory, OnLeave


@pytest.fixture
def directory():
    d = Directory()
    d.add_department("sales")
    d.hire("ana", "sales", 300000)
    d.hire("ben", "sales", 250000)
    return d


def test_no_salary_changes_while_on_leave(directory):
    directory.start_leave("ana")
    assert directory.is_on_leave("ana")
    with pytest.raises(OnLeave):
        directory.set_salary("ana", 310000)
    assert directory.get_salary("ana") == 300000
    directory.end_leave("ana")
    directory.set_salary("ana", 310000)
    assert directory.get_salary("ana") == 310000


def test_staff_can_be_listed_without_those_on_leave(directory):
    directory.start_leave("ana")
    assert directory.get_staff("sales") == ["ana", "ben"]
    assert directory.get_staff("sales", include_on_leave=False) == ["ben"]


def test_new_hires_are_not_on_leave(directory):
    assert not directory.is_on_leave("ben")
