"""Public checks for the c_usage change (booked minutes and room ranking).
Shown to the editor, never to the writer.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_usage/public/test_usage_public.py
"""

from rooms import RoomPlanner


def test_usage_counts_only_minutes_inside_the_window():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("a", "oak", 100, 160)
    p.book("b", "oak", 200, 230)
    assert p.get_booked_minutes("oak", 0, 1000) == 90
    assert p.get_booked_minutes("oak", 130, 210) == 40


def test_usage_ranking_puts_busiest_rooms_first():
    p = RoomPlanner()
    for room in ("oak", "elm", "ash"):
        p.add_room(room)
    p.book("a", "elm", 0, 30)
    p.book("b", "ash", 0, 60)
    assert p.get_usage_ranking(0, 100) == [("ash", 60), ("elm", 30), ("oak", 0)]
