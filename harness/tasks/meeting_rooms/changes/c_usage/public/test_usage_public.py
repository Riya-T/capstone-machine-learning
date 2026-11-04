"""Public checks for the c_usage change (booked slots and usage ranking).
Shown to the editor, never to the writer.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_usage/public/test_usage_public.py
"""

from rooms import RoomPlanner


def test_usage_counts_the_bookings_in_a_stretch():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("a", "oak", 10)
    p.book("b", "oak", 11)
    p.book("c", "oak", 20)
    assert p.get_booked_slots("oak", 10, 12) == 2
    assert p.get_booked_slots("oak", 11, 20) == 1
    assert p.get_booked_slots("oak", 0, 100) == 3
    assert p.get_booked_slots("oak", 12, 20) == 0


def test_usage_ranking_puts_the_busiest_room_first():
    p = RoomPlanner()
    for room in ("oak", "elm", "ash"):
        p.add_room(room)
    p.book("a", "elm", 1)
    p.book("b", "elm", 2)
    p.book("c", "ash", 2)
    assert p.get_usage_ranking(0, 10) == [("elm", 2), ("ash", 1), ("oak", 0)]
