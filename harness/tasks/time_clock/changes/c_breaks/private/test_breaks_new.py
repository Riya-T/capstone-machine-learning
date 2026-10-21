"""Hidden tests for the c_breaks change (unpaid breaks). Never shown to the
writer or the editor.

Usage (with timeclock.py importable, e.g. in the sandbox):
    python -m pytest changes/c_breaks/private/test_breaks_new.py
"""

import pytest
from timeclock import ClockError, TimeClock, VersionConflict

EMPLOYEES = ["ana", "ben"]


@pytest.fixture
def clock():
    """ana is clocked in since minute 100 and is at version 2; ben is new."""
    c = TimeClock()
    for name in EMPLOYEES:
        c.add_employee(name)
    c.clock_in("ana", 100)
    return c


def state(c):
    return {
        e: (
            c.get_shifts(e),
            c.get_open_shift(e),
            c.get_break_minutes(e),
            c.get_paid_minutes(e),
            c.get_overtime_minutes(e),
            c.get_version(e),
        )
        for e in EMPLOYEES
    }


def shift(c, employee_id, start, end, breaks=()):
    c.clock_in(employee_id, start)
    for break_start, break_end in breaks:
        c.start_break(employee_id, break_start)
        c.end_break(employee_id, break_end)
    c.clock_out(employee_id, end)


def test_break_totals_add_up_over_shifts_and_breaks():
    c = TimeClock()
    c.add_employee("ana")
    shift(c, "ana", 0, 500, [(100, 115), (200, 230), (300, 345)])
    shift(c, "ana", 600, 700)
    shift(c, "ana", 800, 900, [(800, 810)])
    assert c.get_shifts("ana") == [(0, 500), (600, 700), (800, 900)]
    assert c.get_worked_minutes("ana") == 700
    assert c.get_break_minutes("ana") == 15 + 30 + 45 + 10
    assert c.get_paid_minutes("ana") == 600


def test_break_overtime_uses_paid_minutes_of_each_shift():
    c = TimeClock(overtime_after=100)
    c.add_employee("ana")
    shift(c, "ana", 0, 150, [(50, 80)])  # 120 paid: 20 overtime
    shift(c, "ana", 200, 330, [(250, 290)])  # 90 paid: no overtime
    shift(c, "ana", 400, 600)  # 200 paid: 100 overtime
    assert c.get_overtime_minutes("ana") == 120
    c.set_overtime_after("ana", 0)
    assert c.get_overtime_minutes("ana") == c.get_paid_minutes("ana") == 410


def test_break_of_the_shift_under_way_is_not_counted(clock):
    clock.start_break("ana", 150)
    clock.end_break("ana", 170)
    clock.start_break("ana", 200)
    assert clock.get_break_minutes("ana") == 0
    assert clock.get_paid_minutes("ana") == 0
    clock.end_break("ana", 210)
    clock.clock_out("ana", 300)
    assert clock.get_break_minutes("ana") == 30
    assert clock.get_paid_minutes("ana") == 170


def test_break_may_start_at_the_clock_in_minute_and_right_after_another(clock):
    clock.start_break("ana", 100)
    clock.end_break("ana", 110)
    clock.start_break("ana", 110)
    clock.end_break("ana", 120)
    clock.clock_out("ana", 120)
    assert clock.get_shifts("ana") == [(100, 120)]
    assert clock.get_paid_minutes("ana") == 0


def test_break_start_errors_come_in_order(clock):
    clock.start_break("ana", 150)
    clock.end_break("ana", 200)
    before = state(clock)
    for call, error in (
        (lambda: clock.start_break("carl", -1), KeyError),
        (lambda: clock.start_break("ana", 300, expected_version=1), VersionConflict),
        (lambda: clock.start_break("ben", -1), ValueError),
        (lambda: clock.start_break("ana", "300"), ValueError),
        (lambda: clock.start_break("ben", 10), ClockError),
        (lambda: clock.start_break("ana", 199), ValueError),
        (lambda: clock.start_break("ana", 50), ValueError),
    ):
        with pytest.raises(error):
            call()
    assert state(clock) == before
    clock.start_break("ana", 250)
    with pytest.raises(ClockError):
        clock.start_break("ana", 260)
    with pytest.raises(ClockError):
        # Already on a break is reported before the early minute.
        clock.start_break("ana", 10)


def test_break_end_errors_come_in_order(clock):
    before = state(clock)
    with pytest.raises(ClockError):
        clock.end_break("ana", 150)
    with pytest.raises(ClockError):
        clock.end_break("ben", 150)
    assert state(clock) == before
    clock.start_break("ana", 150)
    before = state(clock)
    for call, error in (
        (lambda: clock.end_break("carl", -1), KeyError),
        (lambda: clock.end_break("ana", -1, expected_version=2), VersionConflict),
        (lambda: clock.end_break("ana", None), ValueError),
        (lambda: clock.end_break("ana", 150), ValueError),
        (lambda: clock.end_break("ana", 120), ValueError),
    ):
        with pytest.raises(error):
            call()
    assert state(clock) == before


def test_break_rules_for_clocking_out(clock):
    clock.start_break("ana", 150)
    before = state(clock)
    with pytest.raises(ValueError):
        clock.clock_out("ana", -1)
    with pytest.raises(ClockError):
        # On a break is reported before the minute being too early.
        clock.clock_out("ana", 120)
    assert state(clock) == before
    clock.end_break("ana", 200)
    before = state(clock)
    with pytest.raises(ValueError):
        clock.clock_out("ana", 199)
    assert state(clock) == before
    clock.clock_out("ana", 200)
    assert clock.get_shifts("ana") == [(100, 200)]
    assert clock.get_paid_minutes("ana") == 50


def test_break_calls_count_as_changes(clock):
    clock.start_break("ana", 120, expected_version=2)
    clock.end_break("ana", 130, expected_version=3)
    assert clock.get_version("ana") == 4
    with pytest.raises(VersionConflict):
        clock.start_break("ana", 140, expected_version=3)
    assert clock.get_version("ben") == 1


def test_break_is_kept_when_its_shift_is_corrected():
    c = TimeClock()
    c.add_employee("ana")
    shift(c, "ana", 100, 400, [(200, 260)])
    c.correct_shift("ana", 0, 50, 500)
    assert c.get_shifts("ana") == [(50, 500)]
    assert c.get_break_minutes("ana") == 60
    assert c.get_paid_minutes("ana") == 390
    c.correct_shift("ana", 0, 200, 260)
    assert c.get_paid_minutes("ana") == 0


@pytest.mark.parametrize("start, end", [(201, 400), (100, 259), (300, 400)])
def test_break_must_stay_inside_its_corrected_shift(start, end):
    c = TimeClock()
    c.add_employee("ana")
    shift(c, "ana", 100, 400, [(200, 260)])
    version = c.get_version("ana")
    with pytest.raises(ValueError):
        c.correct_shift("ana", 0, start, end)
    assert c.get_shifts("ana") == [(100, 400)]
    assert c.get_break_minutes("ana") == 60
    assert c.get_version("ana") == version


def test_break_totals_need_a_known_employee(clock):
    for read in (clock.get_break_minutes, clock.get_paid_minutes):
        with pytest.raises(KeyError):
            read("carl")
        with pytest.raises(KeyError):
            read(None)
