"""Hidden tests for the c_overtime_rules change (adjustable overtime rule).
Never shown to the writer or the editor.

Usage (with timeclock.py importable, e.g. in the sandbox):
    python -m pytest changes/c_overtime_rules/private/test_overtime_rules_new.py
"""

import pytest
from timeclock import ClockError, TimeClock

BAD_VALUES = [-1, 2.5, "480", True]


def work(c, employee_id, shifts):
    for start, end in shifts:
        c.clock_in(employee_id, start)
        c.clock_out(employee_id, end)


def state(c, ids):
    return {
        e: (c.get_shifts(e), c.get_open_shift(e), c.get_overtime_after(e)) for e in ids
    }


def test_threshold_defaults_to_480():
    c = TimeClock()
    c.add_employee("ana")
    assert c.get_overtime_after("ana") == 480
    work(c, "ana", [(0, 481)])
    assert c.get_overtime_minutes("ana") == 1


def test_threshold_of_the_clock_is_used_by_every_new_employee():
    c = TimeClock(overtime_after=60)
    c.add_employee("ana")
    c.add_employee("ben")
    work(c, "ana", [(0, 100), (200, 230)])
    work(c, "ben", [(0, 60)])
    assert c.get_overtime_minutes("ana") == 40
    assert c.get_overtime_minutes("ben") == 0
    assert c.get_overtime_after("ben") == 60


def test_threshold_of_zero_makes_every_minute_overtime():
    c = TimeClock(overtime_after=0)
    c.add_employee("ana")
    work(c, "ana", [(10, 70), (100, 105)])
    assert c.get_overtime_minutes("ana") == 65
    assert c.get_worked_minutes("ana") == 65


def test_threshold_of_one_employee_overrides_the_clock():
    c = TimeClock(overtime_after=100)
    c.add_employee("ana", overtime_after=0)
    c.add_employee("ben", overtime_after=None)
    work(c, "ana", [(0, 50)])
    work(c, "ben", [(0, 150)])
    assert c.get_overtime_minutes("ana") == 50
    assert c.get_overtime_minutes("ben") == 50
    assert (c.get_overtime_after("ana"), c.get_overtime_after("ben")) == (0, 100)


def test_threshold_is_still_counted_per_shift():
    c = TimeClock(overtime_after=200)
    c.add_employee("ana")
    work(c, "ana", [(0, 150), (300, 450), (500, 800)])
    assert c.get_overtime_minutes("ana") == 100


def test_threshold_set_later_replaces_the_old_one_for_all_shifts():
    c = TimeClock()
    c.add_employee("ana", overtime_after=100)
    c.add_employee("ben")
    work(c, "ana", [(0, 300), (400, 500)])
    assert c.get_overtime_minutes("ana") == 200
    c.set_overtime_after("ana", 250)
    assert c.get_overtime_after("ana") == 250
    assert c.get_overtime_minutes("ana") == 50
    c.set_overtime_after("ana", 0)
    assert c.get_overtime_minutes("ana") == 400
    assert c.get_overtime_after("ben") == 480


def test_threshold_set_later_applies_to_the_shift_under_way():
    c = TimeClock()
    c.add_employee("ana")
    c.clock_in("ana", 0)
    c.set_overtime_after("ana", 30)
    c.clock_out("ana", 100)
    assert c.get_overtime_minutes("ana") == 70


@pytest.mark.parametrize("value", BAD_VALUES + [None])
def test_threshold_of_the_clock_must_be_valid(value):
    with pytest.raises(ValueError):
        TimeClock(overtime_after=value)


@pytest.mark.parametrize("value", BAD_VALUES)
def test_threshold_of_a_new_employee_must_be_valid(value):
    c = TimeClock()
    with pytest.raises(ValueError):
        c.add_employee("ana", overtime_after=value)
    with pytest.raises(KeyError):
        c.get_shifts("ana")
    c.add_employee("ana")
    assert c.get_overtime_after("ana") == 480


@pytest.mark.parametrize("value", BAD_VALUES + [None])
def test_threshold_set_later_must_be_valid(value):
    c = TimeClock()
    c.add_employee("ana", overtime_after=300)
    work(c, "ana", [(0, 400)])
    before = state(c, ["ana"])
    with pytest.raises(ValueError):
        c.set_overtime_after("ana", value)
    assert state(c, ["ana"]) == before
    assert c.get_overtime_minutes("ana") == 100


def test_threshold_errors_come_in_order():
    c = TimeClock()
    c.add_employee("ana", overtime_after=200)
    # An invalid value is reported before the id that was already added.
    with pytest.raises(ValueError):
        c.add_employee("ana", overtime_after=-5)
    with pytest.raises(ClockError):
        c.add_employee("ana", overtime_after=100)
    assert c.get_overtime_after("ana") == 200
    # An unknown employee is reported before an invalid value.
    with pytest.raises(KeyError):
        c.set_overtime_after("carl", -5)
    with pytest.raises(KeyError):
        c.get_overtime_after("carl")
    with pytest.raises(KeyError):
        c.get_overtime_after(None)


def test_threshold_is_kept_per_clock():
    first = TimeClock(overtime_after=10)
    second = TimeClock()
    first.add_employee("ana")
    second.add_employee("ana")
    first.set_overtime_after("ana", 20)
    assert second.get_overtime_after("ana") == 480
    assert first.get_overtime_after("ana") == 20
