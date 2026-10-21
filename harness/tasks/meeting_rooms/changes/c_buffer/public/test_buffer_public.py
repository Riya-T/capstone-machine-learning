"""Public checks for the c_buffer change (adjustable gap between bookings).
Shown to the editor, never to the writer.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_buffer/public/test_buffer_public.py
"""

import pytest
from rooms import RoomBusy, RoomPlanner


def test_buffer_planner_wide_gap():
    p = RoomPlanner(gap=30)
    p.add_room("oak")
    assert p.get_gap("oak") == 30
    p.book("a", "oak", 100, 160)
    with pytest.raises(RoomBusy):
        p.book("b", "oak", 180, 200)
    p.book("b", "oak", 190, 200)


def test_buffer_room_without_a_gap():
    p = RoomPlanner()
    p.add_room("booth", gap=0)
    p.book("a", "booth", 0, 30)
    p.book("b", "booth", 30, 45)
    assert p.get_room_bookings("booth") == ["a", "b"]
