"""Hidden tests for the c_payroll change (payroll figures). Never shown to
the writer or the editor.

Usage (with directory.py importable, e.g. in the sandbox):
    python -m pytest changes/c_payroll/private/test_payroll_new.py
"""

import pytest
from directory import Directory


@pytest.fixture
def directory():
    d = Directory()
    d.add_department("sales")
    d.add_department("ops")
    d.add_department("legal")
    d.hire("ana", "sales", 300000)
    d.hire("ben", "sales", 250000)
    d.hire("cho", "ops", 200000)
    return d


def test_payroll_sums_every_salary_in_the_department(directory):
    directory.hire("dan", "sales", 1)
    assert directory.get_payroll("sales") == 550001
    assert directory.get_payroll("ops") == 200000


def test_an_empty_department_has_no_payroll(directory):
    assert directory.get_payroll("legal") == 0


def test_payroll_leaves_out_employees_on_leave(directory):
    directory.start_leave("ben")
    assert directory.get_payroll("sales") == 300000
    directory.start_leave("ana")
    assert directory.get_payroll("sales") == 0
    assert directory.get_payroll("ops") == 200000


def test_ending_leave_puts_the_salary_back(directory):
    directory.start_leave("ana")
    directory.end_leave("ana")
    assert directory.get_payroll("sales") == 550000


def test_payroll_follows_salary_changes(directory):
    directory.set_salary("ana", 400000)
    assert directory.get_payroll("sales") == 650000
    directory.set_salary("ben", 1)
    assert directory.get_payroll("sales") == 400001


def test_total_payroll_sums_every_department(directory):
    assert directory.get_total_payroll() == 750000
    directory.hire("dan", "legal", 500000)
    assert directory.get_total_payroll() == 1250000
    directory.start_leave("cho")
    assert directory.get_total_payroll() == 1050000


def test_total_payroll_of_an_empty_directory_is_zero():
    d = Directory()
    assert d.get_total_payroll() == 0
    d.add_department("sales")
    assert d.get_total_payroll() == 0


@pytest.mark.parametrize("department", ["hr", None, 1])
def test_payroll_of_a_missing_department_raises_key_error(directory, department):
    with pytest.raises(KeyError):
        directory.get_payroll(department)


def test_salary_history_of_a_new_hire_is_the_hire_salary(directory):
    assert directory.get_salary_history("ana") == [300000]
    assert directory.get_salary_history("cho") == [200000]


def test_salary_history_records_every_change_including_repeats(directory):
    directory.set_salary("ana", 320000)
    directory.set_salary("ana", 320000)
    directory.set_salary("ana", 290000)
    assert directory.get_salary_history("ana") == [300000, 320000, 320000, 290000]
    assert directory.get_salary("ana") == 290000
    assert directory.get_salary_history("ben") == [250000]


def test_failed_salary_changes_add_nothing_to_the_history(directory):
    for call in (
        lambda: directory.set_salary("ana", 0),
        lambda: directory.set_salary("ana", "100"),
        lambda: directory.set_salary("ana", -5),
    ):
        with pytest.raises(ValueError):
            call()
    with pytest.raises(KeyError):
        directory.set_salary("eve", 100000)
    assert directory.get_salary_history("ana") == [300000]
    assert directory.get_salary_history("ben") == [250000]


@pytest.mark.parametrize("employee_id", ["eve", None, 1])
def test_salary_history_of_an_unknown_employee_raises_key_error(directory, employee_id):
    with pytest.raises(KeyError):
        directory.get_salary_history(employee_id)


def test_payroll_figures_do_not_change_the_directory(directory):
    directory.get_payroll("sales")
    directory.get_total_payroll()
    directory.get_salary_history("ana")
    assert directory.get_staff("sales") == ["ana", "ben"]
    assert directory.get_salary("ana") == 300000
    assert directory.get_salary_history("ana") == [300000]
