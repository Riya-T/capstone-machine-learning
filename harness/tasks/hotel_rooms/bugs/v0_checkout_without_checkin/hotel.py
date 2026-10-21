"""Hotel rooms: rooms, bookings by night number, and check-in / check-out.

Planted bug (initial version): check_out only refuses a booking that is
already checked out, so a guest who never checked in can check out. The
public checks never try that, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from hotel import Hotel
    hotel = Hotel()
    hotel.add_room("101")
    booking = hotel.book("101", "ana", 1, 3)
    hotel.check_in(booking)
"""


class HotelError(Exception):
    pass


class RoomUnavailable(HotelError):
    pass


BOOKED = "booked"
CHECKED_IN = "checked_in"
CHECKED_OUT = "checked_out"


def check_night(night):
    if isinstance(night, bool) or not isinstance(night, int) or night < 1:
        raise ValueError(f"night must be an int >= 1, got {night!r}")


def check_guest(guest):
    if not isinstance(guest, str) or not guest:
        raise ValueError("guest must be a non-empty str")


class Hotel:
    def __init__(self):
        self._rooms = {}  # room -> {night: booking id}, in the order added
        self._bookings = {}  # booking id -> {"room", "guest", "nights", "status"}

    def add_room(self, room):
        if not isinstance(room, str) or not room:
            raise ValueError("room must be a non-empty str")
        if room in self._rooms:
            raise HotelError(f"room {room!r} already exists")
        self._rooms[room] = {}

    def book(self, room, guest, first_night, last_night):
        self._require_room(room)
        check_guest(guest)
        check_night(first_night)
        check_night(last_night)
        if last_night < first_night:
            raise ValueError("last_night must not be before first_night")
        nights = range(first_night, last_night + 1)
        taken = self._rooms[room]
        if any(night in taken for night in nights):
            raise RoomUnavailable(f"room {room!r} is not free for every night")
        booking_id = len(self._bookings) + 1
        self._bookings[booking_id] = {
            "room": room,
            "guest": guest,
            "nights": nights,
            "status": BOOKED,
        }
        for night in nights:
            taken[night] = booking_id
        return booking_id

    def check_in(self, booking_id):
        booking = self._require_booking(booking_id)
        if booking["status"] != BOOKED:
            raise HotelError(f"booking {booking_id} is {booking['status']}")
        booking["status"] = CHECKED_IN

    def check_out(self, booking_id):
        booking = self._require_booking(booking_id)
        if booking["status"] == CHECKED_OUT:
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

    def get_rooms(self):
        return list(self._rooms)

    def _require_room(self, room):
        # Non-str names are never stored, so they count as "no such room" too.
        if not isinstance(room, str) or room not in self._rooms:
            raise KeyError(room)

    def _require_booking(self, booking_id):
        if isinstance(booking_id, bool) or booking_id not in self._bookings:
            raise KeyError(booking_id)
        return self._bookings[booking_id]
