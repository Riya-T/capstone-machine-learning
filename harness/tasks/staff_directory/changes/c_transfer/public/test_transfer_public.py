"""Public checks for the c_transfer change (headcount caps and transfers).
Shown to the editor, never to the writer.

Usage (with directory.py importable, e.g. in the sandbox):
    python -m pytest changes/c_transfer/public/test_transfer_public.py
"""

import pytest
from directory import DepartmentFull, Directory


@pytest.fixture
def directory():
    d = Directory()
    d.add_department("sales")
    d.add_department("ops")
    d.hire("ana", "sales", 300000)
    d.hire("ben", "sales", 250000)
    d.hire("cho", "ops", 200000)
    return d


def test_transfer_moves_employees_to_the_end_of_the_new_department(directory):
    directory.transfer(["ben", "ana"], "ops")
    assert directory.get_staff("ops") == ["cho", "ben", "ana"]
    assert directory.get_staff("sales") == []
    assert directory.get_department("ana") == "ops"
    assert directory.get_salary("ana") == 300000


def test_a_transfer_over_the_cap_moves_nobody(directory):
    directory.set_cap("ops", 2)
    with pytest.raises(DepartmentFull):
        directory.transfer(["ana", "ben"], "ops")
    assert directory.get_staff("ops") == ["cho"]
    assert directory.get_staff("sales") == ["ana", "ben"]


def test_hiring_into_a_full_department_raises(directory):
    directory.set_cap("ops", 1)
    with pytest.raises(DepartmentFull):
        directory.hire("dan", "ops", 100000)
    assert directory.get_staff("ops") == ["cho"]
