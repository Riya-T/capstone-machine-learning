"""Public checks for the c_payroll change (payroll figures). Shown to the
editor, never to the writer.

Usage (with directory.py importable, e.g. in the sandbox):
    python -m pytest changes/c_payroll/public/test_payroll_public.py
"""

import pytest
from directory import Directory


@pytest.fixture
def directory():
    d = Directory()
    d.add_department("sales")
    d.add_department("ops")
    d.hire("ana", "sales", 300000)
    d.hire("ben", "sales", 250000)
    d.hire("cho", "ops", 200000)
    return d


def test_payroll_sums_the_salaries_of_a_department(directory):
    assert directory.get_payroll("sales") == 550000
    assert directory.get_payroll("ops") == 200000
    assert directory.get_total_payroll() == 750000


def test_employees_on_leave_are_not_paid(directory):
    directory.start_leave("ana")
    assert directory.get_payroll("sales") == 250000
    assert directory.get_total_payroll() == 450000


def test_salary_history_starts_with_the_hire_salary(directory):
    directory.set_salary("ana", 320000)
    directory.set_salary("ana", 310000)
    assert directory.get_salary_history("ana") == [300000, 320000, 310000]
    assert directory.get_salary_history("ben") == [250000]
