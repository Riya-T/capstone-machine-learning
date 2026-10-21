"""Public checks for the c_breaks change (unpaid breaks). Shown to the
editor, never to the writer.

Usage (with timeclock.py importable, e.g. in the sandbox):
    python -m pytest changes/c_breaks/public/test_breaks_public.py
"""

import pytest
from timeclock import ClockError, TimeClock


def test_break_is_not_paid():
    c = TimeClock()
    c.add_employee("ana")
    c.clock_in("ana", 0)
    c.start_break("ana", 200)
    c.end_break("ana", 230)
    c.clock_out("ana", 400)
    assert c.get_shifts("ana") == [(0, 400)]
    assert c.get_worked_minutes("ana") == 400
    assert c.get_break_minutes("ana") == 30
    assert c.get_paid_minutes("ana") == 370


def test_break_lowers_the_overtime():
    c = TimeClock()
    c.add_employee("ana")
    c.clock_in("ana", 0)
    c.start_break("ana", 240)
    c.end_break("ana", 300)
    c.clock_out("ana", 600)
    assert c.get_overtime_minutes("ana") == 60


def test_break_must_end_before_clocking_out():
    c = TimeClock()
    c.add_employee("ana")
    c.clock_in("ana", 0)
    c.start_break("ana", 100)
    with pytest.raises(ClockError):
        c.clock_out("ana", 200)
    assert c.get_open_shift("ana") == 0
