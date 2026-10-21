"""Hotel rooms with cancellable bookings and room categories.

Planted bug (after c_cancel and c_categories): categories were added
correctly, but while add_room was rewritten to take a category the check
that refuses an existing room name was lost, so a room can be added twice
(wiping its bookings). Never shown to the writer or the editor;
validate-tasks checks that the tests catch it.

Usage:
    from hotel import Hotel
    hotel = Hotel()
    hotel.add_room("101", category="single")
    booking = hotel.book_any("single", "ana", 1, 3)
    hotel.cancel(booking)
"""


class HotelError(Exception):
    pass


class RoomUnavailable(HotelError):
    pass


BOOKED = "booked"
CHECKED_IN = "checked_in"
CHECKED_OUT = "checked_out"
CANCELLED = "cancelled"


def check_night(night):
    if isinstance(night, bool) or not isinstance(night, int) or night < 1:
        raise ValueError(f"night must be an int >= 1, got {night!r}")


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


class Hotel:
    def __init__(self):
        self._rooms = {}  # room -> {night: booking id}, in the order added
        self._categories = {}  # room -> category
        self._bookings = {}  # booking id -> {"room", "guest", "nights", "status"}

    def add_room(self, room, category="standard"):
        check_name(room, "room")
        check_name(category, "category")
        self._rooms[room] = {}
        self._categories[room] = category

    def book(self, room, guest, first_night, last_night):
        self._require_room(room)
        nights = self._check_request(guest, first_night, last_night)
        if not self._is_free(room, nights):
            raise RoomUnavailable(f"room {room!r} is not free for every night")
        return self._record(room, guest, nights)

    def book_any(self, category, guest, first_night, last_night):
        candidates = [room for room in self._rooms if self._categories[room] == category]
        if not candidates:
            raise KeyError(category)
        nights = self._check_request(guest, first_night, last_night)
        for room in candidates:
            if self._is_free(room, nights):
                return self._record(room, guest, nights)
        raise RoomUnavailable(f"no {category!r} room is free for every night")

    def cancel(self, booking_id):
        booking = self._require_booking(booking_id)
        if booking["status"] != BOOKED:
            raise HotelError(f"booking {booking_id} is {booking['status']}")
        booking["status"] = CANCELLED
        taken = self._rooms[booking["room"]]
        for night in booking["nights"]:
            del taken[night]

    def check_in(self, booking_id):
        booking = self._require_booking(booking_id)
        if booking["status"] != BOOKED:
            raise HotelError(f"booking {booking_id} is {booking['status']}")
        booking["status"] = CHECKED_IN

    def check_out(self, booking_id):
        booking = self._require_booking(booking_id)
        if booking["status"] != CHECKED_IN:
            raise HotelError(f"booking {booking_id} is {booking['status']}")
        booking["status"] = CHECKED_OUT

    def get_status(self, booking_id):
        return self._require_booking(booking_id)["status"]

    def get_guest(self, room, night):
        self._require_room(room)
        check_night(night)
        booking_id = self._rooms[room].get(night)
        if booking_id is None:
            return None
        return self._bookings[booking_id]["guest"]

    def get_rooms(self, category=None):
        if category is None:
            return list(self._rooms)
        return [room for room in self._rooms if self._categories[room] == category]

    def get_category(self, room):
        self._require_room(room)
        return self._categories[room]

    def get_categories(self):
        return list(dict.fromkeys(self._categories.values()))

    def _check_request(self, guest, first_night, last_night):
        check_name(guest, "guest")
        check_night(first_night)
        check_night(last_night)
        if last_night < first_night:
            raise ValueError("last_night must not be before first_night")
        return range(first_night, last_night + 1)

    def _is_free(self, room, nights):
        taken = self._rooms[room]
        return not any(night in taken for night in nights)

    def _record(self, room, guest, nights):
        booking_id = len(self._bookings) + 1
        self._bookings[booking_id] = {
            "room": room,
            "guest": guest,
            "nights": nights,
            "status": BOOKED,
        }
        for night in nights:
            self._rooms[room][night] = booking_id
        return booking_id

    def _require_room(self, room):
        # Non-str names are never stored, so they count as "no such room" too.
        if not isinstance(room, str) or room not in self._rooms:
            raise KeyError(room)

    def _require_booking(self, booking_id):
        if isinstance(booking_id, bool) or booking_id not in self._bookings:
            raise KeyError(booking_id)
        return self._bookings[booking_id]
