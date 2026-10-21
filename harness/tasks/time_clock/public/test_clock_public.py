"""Public checks for timeclock.py.

Usage (with timeclock.py importable, e.g. in the sandbox):
    python -m pytest public/test_clock_public.py
"""

import pytest
from timeclock import ClockError, TimeClock


@pytest.fixture
def clock():
    c = TimeClock()
    c.add_employee("ana")
    c.add_employee("ben")
    return c


def test_a_finished_shift_is_recorded(clock):
    clock.clock_in("ana", 60)
    clock.clock_out("ana", 300)
    assert clock.get_shifts("ana") == [(60, 300)]
    assert clock.get_worked_minutes("ana") == 240
    assert clock.get_open_shift("ana") is None


def test_a_shift_under_way_is_not_counted(clock):
    clock.clock_in("ana", 100)
    assert clock.get_open_shift("ana") == 100
    assert clock.get_shifts("ana") == []
    assert clock.get_worked_minutes("ana") == 0


def test_minutes_after_eight_hours_are_overtime(clock):
    clock.clock_in("ben", 0)
    clock.clock_out("ben", 600)
    assert clock.get_overtime_minutes("ben") == 120
    assert clock.get_overtime_minutes("ana") == 0


def test_clocking_out_without_clocking_in_raises(clock):
    with pytest.raises(ClockError):
        clock.clock_out("ana", 50)
    assert clock.get_shifts("ana") == []


def test_clock_out_must_be_after_clock_in(clock):
    clock.clock_in("ana", 200)
    with pytest.raises(ValueError):
        clock.clock_out("ana", 200)
    assert clock.get_open_shift("ana") == 200


def test_unknown_employee_raises_key_error(clock):
    with pytest.raises(KeyError):
        clock.get_shifts("carl")
