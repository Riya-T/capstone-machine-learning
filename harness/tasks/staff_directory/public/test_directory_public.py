"""Public checks for directory.py.

Usage (with directory.py importable, e.g. in the sandbox):
    python -m pytest public/test_directory_public.py
"""

import pytest
from directory import Directory


@pytest.fixture
def directory():
    d = Directory()
    d.add_department("sales")
    d.add_department("ops")
    d.hire("ana", "sales", 300000)
    d.hire("ben", "ops", 250000)
    return d


def test_a_hired_employee_has_a_department_and_a_salary(directory):
    assert directory.get_department("ana") == "sales"
    assert directory.get_salary("ana") == 300000


def test_staff_are_listed_in_hire_order(directory):
    directory.hire("cho", "sales", 280000)
    assert directory.get_staff("sales") == ["ana", "cho"]
    assert directory.get_staff("ops") == ["ben"]
    assert directory.get_departments() == ["sales", "ops"]


def test_set_salary_replaces_the_salary(directory):
    directory.set_salary("ana", 320000)
    assert directory.get_salary("ana") == 320000


def test_hiring_into_a_department_that_does_not_exist_raises_key_error(directory):
    with pytest.raises(KeyError):
        directory.hire("cho", "legal", 100000)


def test_salaries_must_be_positive(directory):
    with pytest.raises(ValueError):
        directory.hire("cho", "sales", 0)
    with pytest.raises(ValueError):
        directory.hire("cho", "sales", -100)
    assert directory.get_staff("sales") == ["ana"]


def test_unknown_employee_raises_key_error(directory):
    with pytest.raises(KeyError):
        directory.get_salary("dan")
