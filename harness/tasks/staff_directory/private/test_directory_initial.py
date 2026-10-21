"""Hidden tests for the initial staff_directory spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with directory.py importable, e.g. in the sandbox):
    python -m pytest private/test_directory_initial.py
"""

import pytest
from directory import Directory, DirectoryError

BAD_SALARIES = [0, -1, 2.5, "100", None]


@pytest.fixture
def directory():
    d = Directory()
    d.add_department("sales")
    d.add_department("ops")
    d.add_department("legal")
    d.hire("ana", "sales", 300000)
    d.hire("ben", "ops", 250000)
    d.hire("cho", "sales", 280000)
    return d


def state(d):
    """Every department's staff and every employee's record, to check that a
    failed call changed nothing."""
    staff = {dept: d.get_staff(dept) for dept in d.get_departments()}
    people = {
        emp: (d.get_department(emp), d.get_salary(emp))
        for dept in d.get_departments()
        for emp in d.get_staff(dept)
    }
    return staff, people


# --- departments ------------------------------------------------------------


def test_departments_are_listed_in_the_order_added():
    d = Directory()
    for name in ["ops", "sales", "legal"]:
        d.add_department(name)
    assert d.get_departments() == ["ops", "sales", "legal"]


def test_a_new_department_has_no_staff(directory):
    assert directory.get_staff("legal") == []


@pytest.mark.parametrize("bad_name", [""])
def test_invalid_department_names_are_rejected(bad_name):
    d = Directory()
    with pytest.raises(ValueError):
        d.add_department(bad_name)
    assert d.get_departments() == []


def test_adding_a_department_twice_is_rejected(directory):
    with pytest.raises(DirectoryError):
        directory.add_department("sales")
    assert directory.get_departments() == ["sales", "ops", "legal"]
    assert directory.get_staff("sales") == ["ana", "cho"]


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.get_staff("hr"),
        lambda d: d.get_staff(None),
        lambda d: d.get_staff(1),
        lambda d: d.hire("dan", "hr", 100000),
        lambda d: d.hire("dan", None, 100000),
    ],
)
def test_departments_that_do_not_exist_raise_key_error(directory, call):
    before = state(directory)
    with pytest.raises(KeyError):
        call(directory)
    assert state(directory) == before


# --- employees --------------------------------------------------------------


def test_staff_are_listed_per_department_in_hire_order(directory):
    directory.hire("dan", "ops", 200000)
    directory.hire("eve", "sales", 310000)
    assert directory.get_staff("sales") == ["ana", "cho", "eve"]
    assert directory.get_staff("ops") == ["ben", "dan"]
    assert directory.get_staff("legal") == []


def test_hire_records_department_and_salary(directory):
    assert directory.get_department("cho") == "sales"
    assert directory.get_salary("cho") == 280000
    assert directory.get_department("ben") == "ops"


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_employee_ids_are_rejected(directory, bad_id):
    before = state(directory)
    with pytest.raises(ValueError):
        directory.hire(bad_id, "sales", 100000)
    assert state(directory) == before


def test_hiring_an_employed_id_again_is_rejected(directory):
    before = state(directory)
    with pytest.raises(DirectoryError):
        directory.hire("ana", "sales", 100000)
    with pytest.raises(DirectoryError):
        directory.hire("ana", "ops", 100000)  # not even into another department
    assert state(directory) == before
    assert directory.get_salary("ana") == 300000


@pytest.mark.parametrize("salary", BAD_SALARIES)
def test_invalid_salaries_are_rejected_when_hiring(directory, salary):
    before = state(directory)
    with pytest.raises(ValueError):
        directory.hire("dan", "sales", salary)
    assert state(directory) == before
    with pytest.raises(KeyError):
        directory.get_department("dan")


@pytest.mark.parametrize("salary", BAD_SALARIES)
def test_invalid_salaries_are_rejected_when_set(directory, salary):
    before = state(directory)
    with pytest.raises(ValueError):
        directory.set_salary("ana", salary)
    assert state(directory) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.set_salary("dan", 100000),
        lambda d: d.get_salary("dan"),
        lambda d: d.get_department("dan"),
        lambda d: d.get_salary(None),
        lambda d: d.get_department(1),
        lambda d: d.set_salary(None, 100000),
    ],
)
def test_ids_that_are_not_employed_raise_key_error(directory, call):
    before = state(directory)
    with pytest.raises(KeyError):
        call(directory)
    assert state(directory) == before


def test_set_salary_changes_only_that_employee(directory):
    directory.set_salary("ana", 350000)
    assert directory.get_salary("ana") == 350000
    assert directory.get_salary("cho") == 280000
    assert directory.get_department("ana") == "sales"
    assert directory.get_staff("sales") == ["ana", "cho"]


def test_a_salary_can_be_lowered_and_set_again(directory):
    directory.set_salary("ben", 1)
    assert directory.get_salary("ben") == 1
    directory.set_salary("ben", 250000)
    assert directory.get_salary("ben") == 250000


# --- error order ------------------------------------------------------------


def test_an_empty_id_is_reported_before_a_missing_department(directory):
    with pytest.raises(ValueError):
        directory.hire("", "hr", 100000)


def test_a_missing_department_is_reported_before_a_bad_salary(directory):
    with pytest.raises(KeyError):
        directory.hire("dan", "hr", -1)


def test_a_bad_salary_is_reported_before_a_duplicate_id(directory):
    with pytest.raises(ValueError):
        directory.hire("ana", "ops", -1)
    assert directory.get_department("ana") == "sales"


def test_an_unknown_employee_is_reported_before_a_bad_salary(directory):
    with pytest.raises(KeyError):
        directory.set_salary("dan", -1)


def test_failed_calls_change_nothing(directory):
    before = state(directory)
    for call in (
        lambda: directory.hire("ana", "ops", 100000),
        lambda: directory.hire("dan", "hr", 100000),
        lambda: directory.hire("dan", "ops", 0),
        lambda: directory.set_salary("ana", 0),
        lambda: directory.set_salary("dan", 100000),
        lambda: directory.add_department("ops"),
        lambda: directory.add_department(""),
    ):
        with pytest.raises((ValueError, KeyError, DirectoryError)):
            call()
    assert state(directory) == before


def test_directories_do_not_share_data():
    first, second = Directory(), Directory()
    first.add_department("sales")
    first.hire("ana", "sales", 100000)
    assert second.get_departments() == []
    with pytest.raises(KeyError):
        second.get_salary("ana")
    second.add_department("sales")
    assert second.get_staff("sales") == []
