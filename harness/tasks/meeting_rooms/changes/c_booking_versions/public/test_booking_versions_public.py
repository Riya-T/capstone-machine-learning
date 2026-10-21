"""Public checks for the c_booking_versions change (booking versions and
conflict detection). Shown to the editor, never to the writer.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_booking_versions/public/test_booking_versions_public.py
"""

import pytest
from rooms import RoomPlanner, VersionConflict


def test_versioned_booking_starts_at_one_and_counts_moves():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("a", "oak", 100, 160)
    assert p.get_version("a") == 1
    p.reschedule("a", 200, 260)
    assert p.get_version("a") == 2


def test_versioned_booking_refuses_a_stale_move():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("a", "oak", 100, 160)
    p.reschedule("a", 200, 260, expected_version=1)
    with pytest.raises(VersionConflict):
        p.reschedule("a", 300, 360, expected_version=1)
    assert p.get_booking("a") == ("oak", 200, 260)
