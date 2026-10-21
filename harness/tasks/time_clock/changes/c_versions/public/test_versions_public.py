"""Public checks for the c_versions change (shift corrections and version
numbers). Shown to the editor, never to the writer.

Usage (with timeclock.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/public/test_versions_public.py
"""

import pytest
from timeclock import TimeClock, VersionConflict


def test_version_goes_up_with_each_change():
    c = TimeClock()
    c.add_employee("ana")
    assert c.get_version("ana") == 1
    c.clock_in("ana", 0)
    c.clock_out("ana", 100, expected_version=2)
    assert c.get_version("ana") == 3


def test_version_that_is_out_of_date_is_refused():
    c = TimeClock()
    c.add_employee("ana")
    c.clock_in("ana", 0)
    with pytest.raises(VersionConflict):
        c.clock_out("ana", 100, expected_version=1)
    assert c.get_open_shift("ana") == 0
    assert c.get_version("ana") == 2


def test_correction_replaces_a_finished_shift():
    c = TimeClock()
    c.add_employee("ana")
    c.clock_in("ana", 0)
    c.clock_out("ana", 600)
    c.correct_shift("ana", 0, 30, 480)
    assert c.get_shifts("ana") == [(30, 480)]
    assert c.get_worked_minutes("ana") == 450
    assert c.get_overtime_minutes("ana") == 0
