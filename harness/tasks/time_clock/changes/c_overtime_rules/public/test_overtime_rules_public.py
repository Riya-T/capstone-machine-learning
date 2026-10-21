"""Public checks for the c_overtime_rules change (adjustable overtime rule).
Shown to the editor, never to the writer.

Usage (with timeclock.py importable, e.g. in the sandbox):
    python -m pytest changes/c_overtime_rules/public/test_overtime_rules_public.py
"""

from timeclock import TimeClock


def test_threshold_set_for_the_whole_clock():
    c = TimeClock(overtime_after=300)
    c.add_employee("ana")
    c.clock_in("ana", 0)
    c.clock_out("ana", 400)
    assert c.get_overtime_after("ana") == 300
    assert c.get_overtime_minutes("ana") == 100


def test_threshold_set_for_one_employee():
    c = TimeClock()
    c.add_employee("ana", overtime_after=600)
    c.add_employee("ben")
    for name in ["ana", "ben"]:
        c.clock_in(name, 0)
        c.clock_out(name, 650)
    assert c.get_overtime_minutes("ana") == 50
    assert c.get_overtime_minutes("ben") == 170
    assert c.get_overtime_after("ben") == 480


def test_threshold_change_applies_to_earlier_shifts():
    c = TimeClock()
    c.add_employee("ana")
    c.clock_in("ana", 0)
    c.clock_out("ana", 500)
    c.set_overtime_after("ana", 450)
    assert c.get_overtime_minutes("ana") == 50
