"""Hidden tests for the c_categories change (room categories). Never shown
to the writer or the editor.

Usage (with hotel.py importable, e.g. in the sandbox):
    python -m pytest changes/c_categories/private/test_categories_new.py
"""

import pytest
from hotel import Hotel, RoomUnavailable

NIGHTS = range(1, 9)


@pytest.fixture
def hotel():
    hot = Hotel()
    hot.add_room("101", category="single")
    hot.add_room("201", category="suite")
    hot.add_room("102", category="single")
    hot.add_room("103", category="single")
    return hot


def state(hot, booking_ids=()):
    rooms = {room: [hot.get_guest(room, n) for n in NIGHTS] for room in hot.get_rooms()}
    return rooms, [hot.get_status(b) for b in booking_ids]


def test_the_default_category_is_standard(hotel):
    hotel.add_room("301")
    assert hotel.get_category("301") == "standard"
    assert hotel.get_rooms(category="standard") == ["301"]
    assert hotel.get_categories() == ["single", "suite", "standard"]


def test_rooms_are_listed_per_category_in_the_order_added(hotel):
    assert hotel.get_rooms(category="single") == ["101", "102", "103"]
    assert hotel.get_rooms(category="suite") == ["201"]
    assert hotel.get_rooms() == ["101", "201", "102", "103"]
    assert hotel.get_rooms(category=None) == ["101", "201", "102", "103"]


def test_a_category_nobody_uses_lists_no_rooms(hotel):
    assert hotel.get_rooms(category="penthouse") == []
    assert hotel.get_categories() == ["single", "suite"]


@pytest.mark.parametrize("category", ["", None, 3])
def test_invalid_categories_are_rejected_when_adding_a_room(hotel, category):
    with pytest.raises(ValueError):
        hotel.add_room("301", category=category)
    assert hotel.get_rooms() == ["101", "201", "102", "103"]


def test_get_category_of_an_unknown_room_raises_key_error(hotel):
    with pytest.raises(KeyError):
        hotel.get_category("999")
    with pytest.raises(KeyError):
        hotel.get_category(None)


def test_book_any_skips_rooms_that_are_not_free(hotel):
    hotel.book("101", "ana", 1, 5)
    hotel.book("102", "ben", 3, 3)
    booking = hotel.book_any("single", "cho", 2, 4)
    assert booking == 3
    assert hotel.get_guest("103", 2) == "cho"
    assert hotel.get_status(booking) == "booked"


def test_book_any_prefers_the_earliest_added_room(hotel):
    first = hotel.book_any("single", "ana", 1, 2)
    second = hotel.book_any("single", "ben", 1, 2)
    assert (first, second) == (1, 2)
    assert hotel.get_guest("101", 1) == "ana"
    assert hotel.get_guest("102", 1) == "ben"
    assert hotel.get_guest("103", 1) is None


def test_book_any_only_uses_rooms_of_that_category(hotel):
    hotel.book("201", "ana", 1, 1)
    before = state(hotel, [1])
    with pytest.raises(RoomUnavailable):
        hotel.book_any("suite", "ben", 1, 1)
    assert state(hotel, [1]) == before


def test_book_any_with_an_unknown_category_raises_key_error(hotel):
    with pytest.raises(KeyError):
        hotel.book_any("penthouse", "ana", 1, 2)
    with pytest.raises(KeyError):
        hotel.book_any(None, "ana", 1, 2)
    assert all(hotel.get_guest(r, 1) is None for r in hotel.get_rooms())


@pytest.mark.parametrize(
    "guest, first, last, error",
    [("", 1, 2, ValueError), ("ana", 0, 2, ValueError), ("ana", 3, 2, ValueError)],
)
def test_book_any_checks_guest_and_nights(hotel, guest, first, last, error):
    before = state(hotel)
    with pytest.raises(error):
        hotel.book_any("single", guest, first, last)
    assert state(hotel) == before


def test_book_any_reports_errors_in_order(hotel):
    with pytest.raises(KeyError):
        hotel.book_any("penthouse", "", 2, 1)
    with pytest.raises(ValueError):
        hotel.book_any("suite", "", 2, 1)
    hotel.book("201", "ana", 1, 3)
    with pytest.raises(ValueError):
        hotel.book_any("suite", "ben", 3, 1)


def test_a_cancelled_room_is_free_for_book_any(hotel):
    for room in ["101", "102", "103"]:
        hotel.book(room, "ana", 1, 2)
    with pytest.raises(RoomUnavailable):
        hotel.book_any("single", "ben", 2, 2)
    hotel.cancel(2)
    assert hotel.book_any("single", "ben", 2, 2) == 4
    assert hotel.get_guest("102", 2) == "ben"
