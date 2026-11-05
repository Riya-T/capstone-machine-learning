"""Public checks for the c_buffer change (adjustable gaps between bookings).
Shown to the editor, never to the writer.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_buffer/public/test_buffer_public.py
"""

import pytest
from rooms import RoomBusy, RoomPlanner


def test_buffer_planner_wide_gap():
    p = RoomPlanner(gap=1)
    p.add_room("oak")
    assert p.get_gap("oak") == 1
    p.book("a", "oak", 10)
    with pytest.raises(RoomBusy):
        p.book("b", "oak", 11)
    with pytest.raises(RoomBusy):
        p.book("b", "oak", 9)
    p.book("b", "oak", 12)
    p.book("c", "oak", 8)


def test_buffer_planner_gap_below_zero_is_refused():
    with pytest.raises(ValueError):
        RoomPlanner(gap=-2)


def test_buffer_gap_of_one_room():
    p = RoomPlanner()
    p.add_room("hall", gap=2)
    p.add_room("oak")
    assert p.get_gap("oak") == 0
    p.book("a", "hall", 5)
    with pytest.raises(RoomBusy):
        p.book("b", "hall", 7)
    p.book("b", "hall", 8)
    p.book("c", "oak", 5)
    p.book("d", "oak", 6)
    assert p.get_free_rooms(7) == ["oak"]
    assert p.get_free_rooms(11) == ["hall", "oak"]
