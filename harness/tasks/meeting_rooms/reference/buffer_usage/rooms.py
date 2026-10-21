"""Meeting rooms with booked-minute reports and an adjustable gap between
bookings.

Correct solution for meeting_rooms after c_usage and c_buffer.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from rooms import RoomPlanner
    planner = RoomPlanner(gap=15)
    planner.add_room("booth", gap=0)
    planner.book("call", "booth", 540, 570)
    planner.reschedule("call", 600, 630)
    planner.get_usage_ranking(0, 1440)
"""


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


def check_gap(gap):
    if isinstance(gap, bool) or not isinstance(gap, int) or gap < 0:
        raise ValueError(f"gap must be an int >= 0, got {gap!r}")


def clash(start, end, other_start, other_end, gap):
    """True when two bookings of one room are closer than `gap` minutes."""
    return start < other_end + gap and other_start < end + gap


class _Room:
    def __init__(self, gap):
        self.gap = gap
        self.bookings = []  # booking ids, in booking order


class _Booking:
    def __init__(self, room, start, end):
        self.room = room
        self.start = start
        self.end = end


class RoomPlanner:
    def __init__(self, gap=10):
        check_gap(gap)
        self._gap = gap
        self._rooms = {}  # room name -> _Room, in the order added
        self._bookings = {}  # booking id -> _Booking

    def add_room(self, room, gap=None):
        check_id(room, "room")
        if gap is not None:
            check_gap(gap)
        if room in self._rooms:
            raise BookingError(f"room {room!r} already exists")
        self._rooms[room] = _Room(self._gap if gap is None else gap)

    def book(self, booking_id, room, start, end):
        self._require_room(room)
        check_id(booking_id, "booking id")
        check_times(start, end)
        if booking_id in self._bookings:
            raise BookingError(f"booking id {booking_id!r} is already used")
        self._require_free(room, start, end)
        self._rooms[room].bookings.append(booking_id)
        self._bookings[booking_id] = _Booking(room, start, end)

    def reschedule(self, booking_id, start, end):
        booking = self._require_booking(booking_id)
        check_times(start, end)
        self._require_free(booking.room, start, end, ignore=booking_id)
        booking.start, booking.end = start, end

    def get_booking(self, booking_id):
        booking = self._require_booking(booking_id)
        return (booking.room, booking.start, booking.end)

    def get_room_bookings(self, room):
        self._require_room(room)
        return sorted(self._rooms[room].bookings, key=lambda b: self._bookings[b].start)

    def get_free_rooms(self, start, end):
        check_times(start, end)
        return [room for room in self._rooms if self._is_free(room, start, end)]

    def get_rooms(self):
        return list(self._rooms)

    def get_gap(self, room):
        self._require_room(room)
        return self._rooms[room].gap

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
        for booking_id in self._rooms[room].bookings:
            booking = self._bookings[booking_id]
            total += max(0, min(end, booking.end) - max(start, booking.start))
        return total

    def _is_free(self, room, start, end, ignore=None):
        record = self._rooms[room]
        for other in record.bookings:
            if other == ignore:
                continue
            booking = self._bookings[other]
            if clash(start, end, booking.start, booking.end, record.gap):
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
