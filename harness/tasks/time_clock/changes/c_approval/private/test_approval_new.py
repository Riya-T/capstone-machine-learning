"""Hidden tests for the c_approval change (approving and removing shifts).
Never shown to the writer or the editor.

Usage (with timeclock.py importable, e.g. in the sandbox):
    python -m pytest changes/c_approval/private/test_approval_new.py
"""

import pytest
from timeclock import ClockError, ShiftApproved, TimeClock

EMPLOYEES = ["ana", "ben"]


@pytest.fixture
def clock():
    """ana has shifts (0, 100), (200, 800) and (900, 1000); ben has none."""
    c = TimeClock()
    for name in EMPLOYEES:
        c.add_employee(name)
    for start, end in [(0, 100), (200, 800), (900, 1000)]:
        c.clock_in("ana", start)
        c.clock_out("ana", end)
    return c


def state(c):
    return {
        e: (c.get_shifts(e), c.get_unapproved_shifts(e), c.get_open_shift(e)) for e in EMPLOYEES
    }


def test_approval_is_off_for_new_shifts(clock):
    assert clock.get_unapproved_shifts("ana") == clock.get_shifts("ana")
    assert clock.get_unapproved_shifts("ben") == []
    assert clock.approve_shifts("ben") == 0


def test_approval_skips_the_shift_under_way(clock):
    clock.clock_in("ana", 1100)
    assert clock.approve_shifts("ana") == 3
    clock.clock_out("ana", 1200)
    assert clock.get_unapproved_shifts("ana") == [(1100, 1200)]
    assert clock.approve_shifts("ana") == 1
    assert clock.get_unapproved_shifts("ana") == []


def test_approval_of_one_employee_leaves_others_alone(clock):
    clock.clock_in("ben", 0)
    clock.clock_out("ben", 50)
    clock.approve_shifts("ana")
    assert clock.get_unapproved_shifts("ben") == [(0, 50)]


def test_approval_does_not_change_the_totals(clock):
    worked, overtime = clock.get_worked_minutes("ana"), clock.get_overtime_minutes("ana")
    clock.approve_shifts("ana")
    assert (clock.get_worked_minutes("ana"), clock.get_overtime_minutes("ana")) == (
        worked,
        overtime,
    )
    assert clock.get_shifts("ana") == [(0, 100), (200, 800), (900, 1000)]


def test_approval_status_stays_with_each_shift(clock):
    clock.approve_shifts("ana")
    for start, end in [(1100, 1150), (1200, 1300)]:
        clock.clock_in("ana", start)
        clock.clock_out("ana", end)
    clock.remove_shift("ana", 3)
    assert clock.get_shifts("ana") == [(0, 100), (200, 800), (900, 1000), (1200, 1300)]
    assert clock.get_unapproved_shifts("ana") == [(1200, 1300)]
    for index in range(3):
        with pytest.raises(ShiftApproved):
            clock.remove_shift("ana", index)
    clock.remove_shift("ana", 3)
    assert clock.get_unapproved_shifts("ana") == []


def test_approval_removal_updates_the_totals(clock):
    assert clock.get_overtime_minutes("ana") == 120
    clock.remove_shift("ana", 1)
    assert clock.get_shifts("ana") == [(0, 100), (900, 1000)]
    assert clock.get_worked_minutes("ana") == 200
    assert clock.get_overtime_minutes("ana") == 0
    assert clock.get_unapproved_shifts("ana") == [(0, 100), (900, 1000)]


def test_approval_removal_lets_the_next_clock_in_go_back(clock):
    clock.remove_shift("ana", 2)
    clock.clock_in("ana", 850)
    assert clock.get_open_shift("ana") == 850


def test_approval_removal_leaves_the_shift_under_way_alone(clock):
    clock.clock_in("ana", 1100)
    clock.remove_shift("ana", 0)
    assert clock.get_open_shift("ana") == 1100
    clock.clock_out("ana", 1150)
    assert clock.get_shifts("ana") == [(200, 800), (900, 1000), (1100, 1150)]


@pytest.mark.parametrize("index", [-1, 3, "0", None, 0.0])
def test_approval_removal_needs_the_position_of_a_finished_shift(clock, index):
    before = state(clock)
    with pytest.raises(IndexError):
        clock.remove_shift("ana", index)
    assert state(clock) == before


def test_approval_removal_errors_come_in_order(clock):
    clock.approve_shifts("ana")
    before = state(clock)
    with pytest.raises(KeyError):
        clock.remove_shift("carl", 99)
    with pytest.raises(IndexError):
        clock.remove_shift("ana", 3)
    with pytest.raises(IndexError):
        clock.remove_shift("ben", 0)
    with pytest.raises(ShiftApproved):
        clock.remove_shift("ana", 2)
    assert state(clock) == before
    assert issubclass(ShiftApproved, ClockError)


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.approve_shifts("carl"),
        lambda c: c.get_unapproved_shifts("carl"),
        lambda c: c.remove_shift("carl", 0),
        lambda c: c.approve_shifts(None),
    ],
)
def test_approval_needs_a_known_employee(clock, call):
    before = state(clock)
    with pytest.raises(KeyError):
        call(clock)
    assert state(clock) == before
