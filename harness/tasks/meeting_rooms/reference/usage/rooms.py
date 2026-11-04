"""Meeting rooms: bookings by the slot, one meeting per slot of a room.

Correct solution for meeting_rooms after c_usage.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.
"""

GAP = 0  # free slots needed between two bookings of the same room


class BookingError(Exception):
    pass


class RoomBusy(BookingError):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_slot(slot):
    if not isinstance(slot, int) or slot < 0:
        raise ValueError(f"slot must be an int >= 0, got {slot!r}")


def check_window(first, last):
    check_slot(first)
    if not isinstance(last, int) or last <= first:
        raise ValueError(f"last must be an int > first, got {last!r}")


class RoomPlanner:
    def __init__(self):
        self._rooms = {}  # room name -> list of booking ids, in booking order
        self._bookings = {}  # booking id -> (room, slot)

    def add_room(self, room):
        check_id(room, "room")
        if room in self._rooms:
            raise BookingError(f"room {room!r} already exists")
        self._rooms[room] = []

    def book(self, booking_id, room, slot):
        self._require_room(room)
        check_id(booking_id, "booking id")
        check_slot(slot)
        if booking_id in self._bookings:
            raise BookingError(f"booking {booking_id!r} already exists")
        self._require_free(room, slot)
        self._rooms[room].append(booking_id)
        self._bookings[booking_id] = (room, slot)

    def get_booking(self, booking_id):
        return self._require_booking(booking_id)

    def get_bookings(self):
        return list(self._bookings)

    def get_free_rooms(self, slot):
        check_slot(slot)
        return [room for room in self._rooms if self._is_free(room, slot)]

    def get_rooms(self):
        return list(self._rooms)

    def get_booked_slots(self, room, first, last):
        self._require_room(room)
        check_window(first, last)
        return self._booked_slots(room, first, last)

    def get_usage_ranking(self, first, last):
        check_window(first, last)
        usage = [(room, self._booked_slots(room, first, last)) for room in self._rooms]
        # sorted() is stable, so rooms with equal counts keep the order they were added.
        return sorted(usage, key=lambda pair: -pair[1])

    def _booked_slots(self, room, first, last):
        return sum(1 for b in self._rooms[room] if first <= self._bookings[b][1] < last)

    def _is_free(self, room, slot, ignore=None, gap=GAP):
        for other in self._rooms[room]:
            if other == ignore:
                continue
            if abs(self._bookings[other][1] - slot) <= gap:
                return False
        return True

    def _require_free(self, room, slot, ignore=None):
        if not self._is_free(room, slot, ignore):
            raise RoomBusy(f"room {room!r} is not free in slot {slot}")

    def _require_room(self, room):
        # Non-str names are never stored, so they count as missing too.
        if not isinstance(room, str) or room not in self._rooms:
            raise KeyError(room)

    def _require_booking(self, booking_id):
        if not isinstance(booking_id, str) or booking_id not in self._bookings:
            raise KeyError(booking_id)
        return self._bookings[booking_id]
