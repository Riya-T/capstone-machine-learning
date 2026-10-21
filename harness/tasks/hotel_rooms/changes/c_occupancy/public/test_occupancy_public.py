"""Public checks for the c_occupancy change (occupancy figures). Shown to
the editor, never to the writer.

Usage (with hotel.py importable, e.g. in the sandbox):
    python -m pytest changes/c_occupancy/public/test_occupancy_public.py
"""

from hotel import Hotel


def test_occupancy_counts_rooms_taken_on_a_night():
    hot = Hotel()
    hot.add_room("101")
    hot.add_room("102")
    hot.add_room("103")
    hot.book("101", "ana", 1, 3)
    hot.book("102", "ben", 2, 2)
    assert hot.get_occupancy(1) == 1
    assert hot.get_occupancy(2) == 2
    assert hot.get_occupancy(4) == 0


def test_nights_are_summed_per_room_and_per_guest():
    hot = Hotel()
    hot.add_room("101")
    hot.add_room("102")
    hot.book("101", "ana", 1, 3)
    hot.book("101", "ben", 5, 5)
    hot.book("102", "ana", 2, 3)
    assert hot.get_nights_booked("101") == 4
    assert hot.get_nights_booked("102") == 2
    assert hot.get_guest_nights("ana") == 5
    assert hot.get_guest_nights("nobody") == 0
