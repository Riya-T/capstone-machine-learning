"""Public checks for the c_booking_versions change (moving bookings, with
versions). Shown to the editor, never to the writer.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_booking_versions/public/test_booking_versions_public.py
"""

import pytest
from rooms import RoomBusy, RoomPlanner, VersionConflict


def test_versioned_booking_starts_at_one_and_counts_moves():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("a", "oak", 10)
    p.book("b", "oak", 11)
    assert p.get_version("a") == 1
    p.reschedule("a", 20)
    assert p.get_booking("a") == ("oak", 20)
    assert p.get_version("a") == 2
    with pytest.raises(RoomBusy):
        p.reschedule("a", 11)
    p.reschedule("a", 20)
    assert p.get_version("a") == 3


def test_versioned_booking_can_move_next_to_its_old_slot():
    p = RoomPlanner()
    p.add_room("oak", gap=1)
    p.book("a", "oak", 10)
    p.book("b", "oak", 14)
    p.reschedule("a", 11)
    assert p.get_booking("a") == ("oak", 11)
    with pytest.raises(RoomBusy):
        p.reschedule("a", 13)
    assert p.get_booking("a") == ("oak", 11)


def test_versioned_booking_refuses_a_stale_move():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("a", "oak", 10)
    p.reschedule("a", 20, expected_version=1)
    with pytest.raises(VersionConflict):
        p.reschedule("a", 30, expected_version=1)
    assert p.get_booking("a") == ("oak", 20)
