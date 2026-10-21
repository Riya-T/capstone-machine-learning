"""Hidden tests for the c_transfer change (headcount caps and transfers).
Never shown to the writer or the editor.

Usage (with directory.py importable, e.g. in the sandbox):
    python -m pytest changes/c_transfer/private/test_transfer_new.py
"""

import pytest
from directory import DepartmentFull, Directory, DirectoryError

BAD_CAPS = [-1, 1.5, "2", True, None]


@pytest.fixture
def directory():
    d = Directory()
    d.add_department("sales")
    d.add_department("ops")
    d.add_department("legal")
    d.hire("ana", "sales", 300000)
    d.hire("ben", "sales", 250000)
    d.hire("cho", "sales", 280000)
    d.hire("dan", "ops", 200000)
    return d


def state(d):
    staff = {dept: d.get_staff(dept) for dept in d.get_departments()}
    people = {
        emp: (d.get_department(emp), d.get_salary(emp))
        for dept in d.get_departments()
        for emp in d.get_staff(dept)
    }
    return staff, people


# --- transfers --------------------------------------------------------------


def test_transfer_moves_several_employees_in_the_order_listed(directory):
    directory.transfer(["cho", "ana"], "ops")
    assert directory.get_staff("ops") == ["dan", "cho", "ana"]
    assert directory.get_staff("sales") == ["ben"]
    assert directory.get_department("cho") == "ops"
    assert directory.get_department("ana") == "ops"


def test_transfer_from_several_departments_at_once(directory):
    directory.transfer(["dan", "ben"], "legal")
    assert directory.get_staff("legal") == ["dan", "ben"]
    assert directory.get_staff("ops") == []
    assert directory.get_staff("sales") == ["ana", "cho"]


def test_transferred_employees_keep_their_salaries(directory):
    directory.set_salary("ana", 310000)
    directory.transfer(["ana"], "legal")
    assert directory.get_salary("ana") == 310000
    directory.set_salary("ana", 320000)
    assert directory.get_salary("ana") == 320000


def test_a_transfer_that_exactly_fills_the_cap_is_allowed(directory):
    directory.set_cap("ops", 3)
    directory.transfer(["ana", "ben"], "ops")
    assert directory.get_staff("ops") == ["dan", "ana", "ben"]


def test_a_transfer_over_the_cap_moves_nobody(directory):
    directory.set_cap("ops", 2)
    before = state(directory)
    with pytest.raises(DepartmentFull):
        directory.transfer(["ana", "ben"], "ops")
    assert state(directory) == before
    directory.transfer(["ana"], "ops")  # one fits
    assert directory.get_staff("ops") == ["dan", "ana"]


def test_a_cap_of_zero_keeps_a_department_empty(directory):
    directory.set_cap("legal", 0)
    with pytest.raises(DepartmentFull):
        directory.transfer(["ana"], "legal")
    with pytest.raises(DepartmentFull):
        directory.hire("eve", "legal", 100000)
    assert directory.get_staff("legal") == []


@pytest.mark.parametrize("department", ["hr", None, 1])
def test_transfer_to_a_missing_department_raises_key_error(directory, department):
    before = state(directory)
    with pytest.raises(KeyError):
        directory.transfer(["ana"], department)
    assert state(directory) == before


@pytest.mark.parametrize("ids", [[], ["ana", "ana"], ["ana", "ben", "ana"]])
def test_empty_or_repeated_id_lists_are_rejected(directory, ids):
    before = state(directory)
    with pytest.raises(ValueError):
        directory.transfer(ids, "ops")
    assert state(directory) == before


def test_an_unknown_employee_in_the_list_moves_nobody(directory):
    before = state(directory)
    with pytest.raises(KeyError):
        directory.transfer(["ana", "eve"], "ops")
    with pytest.raises(KeyError):
        directory.transfer([None], "ops")
    assert state(directory) == before


def test_an_employee_already_in_the_department_blocks_the_transfer(directory):
    before = state(directory)
    with pytest.raises(DirectoryError):
        directory.transfer(["ana", "dan"], "ops")  # dan is already in ops
    assert state(directory) == before


def test_transfer_errors_are_reported_in_order(directory):
    directory.set_cap("ops", 1)
    with pytest.raises(KeyError):
        directory.transfer([], "hr")  # missing department before empty list
    with pytest.raises(ValueError):
        directory.transfer(["eve", "eve"], "ops")  # repeated ids before unknown id
    with pytest.raises(KeyError):
        directory.transfer(["dan", "eve"], "ops")  # unknown id before already there
    with pytest.raises(DirectoryError) as info:
        directory.transfer(["ana", "dan"], "ops")  # already there before the cap
    assert not isinstance(info.value, DepartmentFull)
    assert state(directory)[0] == {"sales": ["ana", "ben", "cho"], "ops": ["dan"], "legal": []}


# --- caps and hiring ----------------------------------------------------------


def test_departments_without_a_cap_are_unlimited(directory):
    for i in range(20):
        directory.hire(f"emp{i}", "legal", 100000)
    assert len(directory.get_staff("legal")) == 20


def test_hiring_up_to_the_cap_is_allowed_and_then_refused(directory):
    directory.set_cap("ops", 2)
    directory.hire("eve", "ops", 100000)
    before = state(directory)
    with pytest.raises(DepartmentFull):
        directory.hire("fay", "ops", 100000)
    assert state(directory) == before
    with pytest.raises(KeyError):
        directory.get_salary("fay")


def test_the_cap_is_checked_after_the_other_hire_errors(directory):
    directory.set_cap("ops", 1)
    with pytest.raises(ValueError):
        directory.hire("eve", "ops", -1)
    with pytest.raises(DirectoryError) as info:
        directory.hire("ana", "ops", 100000)
    assert not isinstance(info.value, DepartmentFull)


def test_setting_a_cap_again_replaces_it(directory):
    directory.set_cap("ops", 1)
    directory.set_cap("ops", 2)
    directory.hire("eve", "ops", 100000)
    assert directory.get_staff("ops") == ["dan", "eve"]


def test_a_cap_equal_to_the_current_staff_is_allowed_but_lower_is_not(directory):
    directory.set_cap("sales", 3)
    with pytest.raises(DepartmentFull):
        directory.hire("eve", "sales", 100000)
    before = state(directory)
    with pytest.raises(DirectoryError):
        directory.set_cap("sales", 2)
    assert state(directory) == before
    # The old cap of 3 still applies.
    directory.transfer(["ana"], "ops")
    directory.hire("eve", "sales", 100000)
    assert directory.get_staff("sales") == ["ben", "cho", "eve"]


@pytest.mark.parametrize("cap", BAD_CAPS)
def test_invalid_caps_are_rejected(directory, cap):
    with pytest.raises(ValueError):
        directory.set_cap("ops", cap)
    directory.hire("eve", "ops", 100000)  # still no cap
    assert directory.get_staff("ops") == ["dan", "eve"]


def test_set_cap_errors_are_reported_in_order(directory):
    with pytest.raises(KeyError):
        directory.set_cap("hr", -1)
    with pytest.raises(ValueError):
        directory.set_cap("sales", -1)  # bad cap before "too many staff"


def test_department_full_is_a_directory_error():
    assert issubclass(DepartmentFull, DirectoryError)
