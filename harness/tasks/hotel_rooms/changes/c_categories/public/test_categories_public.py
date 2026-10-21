"""Public checks for the c_categories change (room categories). Shown to the
editor, never to the writer.

Usage (with hotel.py importable, e.g. in the sandbox):
    python -m pytest changes/c_categories/public/test_categories_public.py
"""

import pytest
from hotel import Hotel, RoomUnavailable


def test_rooms_can_be_listed_by_category():
    hot = Hotel()
    hot.add_room("101", category="single")
    hot.add_room("201", category="suite")
    hot.add_room("102", category="single")
    hot.add_room("103")
    assert hot.get_rooms() == ["101", "201", "102", "103"]
    assert hot.get_rooms(category="single") == ["101", "102"]
    assert hot.get_category("103") == "standard"
    assert hot.get_categories() == ["single", "suite", "standard"]


def test_book_any_takes_the_first_free_room_of_the_category():
    hot = Hotel()
    hot.add_room("101", category="single")
    hot.add_room("102", category="single")
    hot.book("101", "ana", 1, 3)
    booking = hot.book_any("single", "ben", 2, 4)
    assert booking == 2
    assert hot.get_guest("102", 3) == "ben"
    with pytest.raises(RoomUnavailable):
        hot.book_any("single", "cho", 3, 3)
