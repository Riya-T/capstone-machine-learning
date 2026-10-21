"""Hidden tests for the c_leave change (employees on leave). Never shown to
the writer or the editor.

Usage (with directory.py importable, e.g. in the sandbox):
    python -m pytest changes/c_leave/private/test_leave_new.py
"""

import pytest
from directory import Directory, DirectoryError, OnLeave


@pytest.fixture
def directory():
    d = Directory()
    d.add_department("sales")
    d.add_department("ops")
    d.hire("ana", "sales", 300000)
    d.hire("ben", "sales", 250000)
    d.hire("cho", "sales", 280000)
    d.hire("dan", "ops", 200000)
    return d


def state(d):
    staff = {dept: d.get_staff(dept) for dept in d.get_departments()}
    people = {
        emp: (d.get_department(emp), d.get_salary(emp), d.is_on_leave(emp))
        for dept in d.get_departments()
        for emp in d.get_staff(dept)
    }
    return staff, people


def test_employees_start_out_not_on_leave(directory):
    for emp in ["ana", "ben", "cho", "dan"]:
        assert not directory.is_on_leave(emp)


def test_starting_or_ending_leave_twice_is_harmless(directory):
    directory.start_leave("ana")
    directory.start_leave("ana")
    assert directory.is_on_leave("ana")
    directory.end_leave("ana")
    directory.end_leave("ana")
    assert not directory.is_on_leave("ana")
    assert not directory.is_on_leave("ben")


@pytest.mark.parametrize("method", ["start_leave", "end_leave", "is_on_leave"])
@pytest.mark.parametrize("employee_id", ["eve", None, 1])
def test_ids_that_are_not_employed_raise_key_error(directory, method, employee_id):
    before = state(directory)
    with pytest.raises(KeyError):
        getattr(directory, method)(employee_id)
    assert state(directory) == before


def test_set_salary_on_leave_raises_and_changes_nothing(directory):
    directory.start_leave("ana")
    before = state(directory)
    with pytest.raises(OnLeave):
        directory.set_salary("ana", 350000)
    with pytest.raises(OnLeave):
        directory.set_salary("ana", 300000)  # even the same salary
    assert state(directory) == before


def test_a_bad_salary_is_reported_before_on_leave(directory):
    directory.start_leave("ana")
    with pytest.raises(ValueError):
        directory.set_salary("ana", -1)
    with pytest.raises(ValueError):
        directory.set_salary("ana", "100")


def test_an_unknown_employee_is_reported_before_anything_else(directory):
    directory.start_leave("ana")
    with pytest.raises(KeyError):
        directory.set_salary("eve", -1)


def test_ending_leave_allows_salary_changes_again(directory):
    directory.start_leave("ana")
    directory.end_leave("ana")
    directory.set_salary("ana", 320000)
    assert directory.get_salary("ana") == 320000


def test_leave_affects_only_that_employee(directory):
    directory.start_leave("ben")
    directory.set_salary("ana", 310000)
    directory.set_salary("cho", 290000)
    assert directory.get_salary("ana") == 310000
    assert directory.get_salary("cho") == 290000
    assert not directory.is_on_leave("ana")
    assert directory.is_on_leave("ben")


def test_salary_and_department_are_still_readable_on_leave(directory):
    directory.start_leave("ana")
    assert directory.get_salary("ana") == 300000
    assert directory.get_department("ana") == "sales"
    assert directory.get_staff("sales") == ["ana", "ben", "cho"]


def test_staff_without_those_on_leave_keeps_the_order(directory):
    directory.start_leave("ben")
    assert directory.get_staff("sales", include_on_leave=False) == ["ana", "cho"]
    directory.start_leave("ana")
    directory.start_leave("cho")
    assert directory.get_staff("sales", include_on_leave=False) == []
    assert directory.get_staff("sales", include_on_leave=True) == ["ana", "ben", "cho"]
    assert directory.get_staff("ops", include_on_leave=False) == ["dan"]


def test_ending_leave_puts_the_employee_back_in_the_list(directory):
    directory.start_leave("ben")
    directory.end_leave("ben")
    assert directory.get_staff("sales", include_on_leave=False) == ["ana", "ben", "cho"]


@pytest.mark.parametrize("flag", [0, 1, "yes", None])
def test_the_include_flag_must_be_a_bool(directory, flag):
    with pytest.raises(ValueError):
        directory.get_staff("sales", include_on_leave=flag)


def test_a_missing_department_is_reported_before_a_bad_flag(directory):
    with pytest.raises(KeyError):
        directory.get_staff("hr", include_on_leave=None)


def test_on_leave_is_a_directory_error():
    assert issubclass(OnLeave, DirectoryError)
