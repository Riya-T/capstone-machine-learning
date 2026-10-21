"""Public checks for the c_approval change (approving and removing shifts).
Shown to the editor, never to the writer.

Usage (with timeclock.py importable, e.g. in the sandbox):
    python -m pytest changes/c_approval/public/test_approval_public.py
"""

import pytest
from timeclock import ShiftApproved, TimeClock


@pytest.fixture
def clock():
    c = TimeClock()
    c.add_employee("ana")
    for start, end in [(0, 100), (200, 300)]:
        c.clock_in("ana", start)
        c.clock_out("ana", end)
    return c


def test_approval_covers_every_finished_shift(clock):
    assert clock.get_unapproved_shifts("ana") == [(0, 100), (200, 300)]
    assert clock.approve_shifts("ana") == 2
    assert clock.get_unapproved_shifts("ana") == []
    assert clock.approve_shifts("ana") == 0


def test_approval_allows_removing_only_unapproved_shifts(clock):
    clock.remove_shift("ana", 1)
    assert clock.get_shifts("ana") == [(0, 100)]
    clock.approve_shifts("ana")
    with pytest.raises(ShiftApproved):
        clock.remove_shift("ana", 0)
    assert clock.get_shifts("ana") == [(0, 100)]
