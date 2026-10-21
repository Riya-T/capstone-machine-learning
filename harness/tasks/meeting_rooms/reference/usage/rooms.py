"""Meeting rooms with a tidy-up gap between meetings and booked-minute
reports.

Correct solution for meeting_rooms after c_usage.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from rooms import RoomPlanner
    planner = RoomPlanner()
    planner.add_room("oak")
    planner.book("standup", "oak", 540, 555)
    planner.get_booked_minutes("oak", 480, 1020)
"""

GAP = 10  # minutes needed between two bookings of the same room


class BookingError(Exception):
    pass


class RoomBusy(BookingError):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_times(start, end):
    if not isinstance(start, int) or start < 0:
        raise ValueError(f"start must be an int >= 0, got {start!r}")
    if not isinstance(end, int) or end <= start:
        raise ValueError(f"end must be an int > start, got {end!r}")


def clash(start, end, other_start, other_end):
    """True when two bookings of one room are too close together."""
    return start < other_end + GAP and other_start < end + GAP


class RoomPlanner:
    def __init__(self):
        self._rooms = {}  # room name -> list of booking ids, in booking order
        self._bookings = {}  # booking id -> (room, start, end)

    def add_room(self, room):
        check_id(room, "room")
        if room in self._rooms:
            raise BookingError(f"room {room!r} already exists")
        self._rooms[room] = []

    def book(self, booking_id, room, start, end):
        self._require_room(room)
        check_id(booking_id, "booking id")
        check_times(start, end)
        if booking_id in self._bookings:
            raise BookingError(f"booking {booking_id!r} already exists")
        self._require_free(room, start, end)
        self._rooms[room].append(booking_id)
        self._bookings[booking_id] = (room, start, end)

    def reschedule(self, booking_id, start, end):
        room, _, _ = self._require_booking(booking_id)
        check_times(start, end)
        self._require_free(room, start, end, ignore=booking_id)
        self._bookings[booking_id] = (room, start, end)

    def get_booking(self, booking_id):
        return self._require_booking(booking_id)

    def get_room_bookings(self, room):
        self._require_room(room)
        return sorted(self._rooms[room], key=lambda b: self._bookings[b][1])

    def get_free_rooms(self, start, end):
        check_times(start, end)
        return [room for room in self._rooms if self._is_free(room, start, end)]

    def get_rooms(self):
        return list(self._rooms)

    def get_booked_minutes(self, room, start, end):
        self._require_room(room)
        check_times(start, end)
        return self._minutes(room, start, end)

    def get_usage_ranking(self, start, end):
        check_times(start, end)
        usage = [(room, self._minutes(room, start, end)) for room in self._rooms]
        return sorted(usage, key=lambda pair: -pair[1])  # stable: ties keep room order

    def _minutes(self, room, start, end):
        total = 0
        for booking_id in self._rooms[room]:
            _, booking_start, booking_end = self._bookings[booking_id]
            total += max(0, min(end, booking_end) - max(start, booking_start))
        return total

    def _is_free(self, room, start, end, ignore=None):
        for other in self._rooms[room]:
            if other == ignore:
                continue
            _, other_start, other_end = self._bookings[other]
            if clash(start, end, other_start, other_end):
                return False
        return True

    def _require_free(self, room, start, end, ignore=None):
        if not self._is_free(room, start, end, ignore):
            raise RoomBusy(f"room {room!r} is not free from {start} to {end}")

    def _require_room(self, room):
        # Non-str names are never stored, so they count as missing too.
        if not isinstance(room, str) or room not in self._rooms:
            raise KeyError(room)

    def _require_booking(self, booking_id):
        if not isinstance(booking_id, str) or booking_id not in self._bookings:
            raise KeyError(booking_id)
        return self._bookings[booking_id]
