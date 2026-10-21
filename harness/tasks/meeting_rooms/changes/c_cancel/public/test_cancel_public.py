"""Public checks for the c_cancel change (cancelling bookings). Shown to the
editor, never to the writer.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/public/test_cancel_public.py
"""

import pytest
from rooms import RoomPlanner


def test_cancel_frees_the_room():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("a", "oak", 100, 160)
    p.cancel("a")
    assert p.get_room_bookings("oak") == []
    assert p.get_cancelled("oak") == ["a"]
    p.book("b", "oak", 100, 160)
    with pytest.raises(KeyError):
        p.get_booking("a")


def test_cancel_twice_raises_key_error():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("a", "oak", 100, 160)
    p.cancel("a")
    with pytest.raises(KeyError):
        p.cancel("a")
