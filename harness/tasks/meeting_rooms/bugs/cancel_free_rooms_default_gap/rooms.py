"""Meeting rooms: bookings by the slot, one meeting per slot of a room,
with an adjustable number of free slots between meetings.

Planted bug (after c_buffer, c_booking_versions and c_cancel): cancelling
was added correctly, but get_free_rooms uses the default gap of 0 for
every room instead of the room's own gap.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from rooms import RoomPlanner
    planner = RoomPlanner()
    planner.add_room("blue")
    planner.book("meeting-1", "blue", 2)
"""

DEFAULT_GAP = 0  # free slots between two bookings of a room, unless set otherwise


class BookingError(Exception):
    pass


class RoomBusy(BookingError):
    pass


class VersionConflict(BookingError):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_slot(slot):
    if not isinstance(slot, int) or slot < 0:
        raise ValueError(f"slot must be an int >= 0, got {slot!r}")


def check_gap(gap):
    if isinstance(gap, bool) or not isinstance(gap, int) or gap < 0:
        raise ValueError(f"gap must be an int >= 0, got {gap!r}")


class RoomPlanner:
    def __init__(self, gap=DEFAULT_GAP):
        check_gap(gap)
        self._gap = gap
        self._gaps = {}  # room name -> its gap
        self._rooms = {}  # room name -> list of booking ids, in booking order
        self._bookings = {}  # booking id -> (room, slot)
        self._versions = {}  # booking id -> version
        self._cancelled = {}  # room name -> cancelled booking ids, in cancel order
        self._used_ids = set()  # every booking id ever booked, cancelled ones too

    def add_room(self, room, gap=None):
        check_id(room, "room")
        if gap is None:
            gap = self._gap
        check_gap(gap)
        if room in self._rooms:
            raise BookingError(f"room {room!r} already exists")
        self._rooms[room] = []
        self._gaps[room] = gap
        self._cancelled[room] = []

    def book(self, booking_id, room, slot):
        self._require_room(room)
        check_id(booking_id, "booking id")
        check_slot(slot)
        if booking_id in self._used_ids:
            raise BookingError(f"booking {booking_id!r} already exists")
        self._require_free(room, slot)
        self._rooms[room].append(booking_id)
        self._bookings[booking_id] = (room, slot)
        self._versions[booking_id] = 1
        self._used_ids.add(booking_id)

    def reschedule(self, booking_id, slot, expected_version=None):
        room, _ = self._require_booking(booking_id)
        check_slot(slot)
        self._check_version(booking_id, expected_version)
        self._require_free(room, slot, ignore=booking_id)
        self._bookings[booking_id] = (room, slot)
        self._versions[booking_id] += 1

    def get_version(self, booking_id):
        self._require_booking(booking_id)
        return self._versions[booking_id]

    def _check_version(self, booking_id, expected_version):
        if expected_version is not None and expected_version != self._versions[booking_id]:
            raise VersionConflict(
                f"booking {booking_id!r} is at version {self._versions[booking_id]}, not {expected_version}"
            )

    def cancel(self, booking_id, expected_version=None):
        room, _ = self._require_booking(booking_id)
        self._check_version(booking_id, expected_version)
        self._rooms[room].remove(booking_id)
        del self._bookings[booking_id]
        del self._versions[booking_id]
        self._cancelled[room].append(booking_id)

    def get_cancelled(self, room):
        self._require_room(room)
        return list(self._cancelled[room])

    def get_booking(self, booking_id):
        return self._require_booking(booking_id)

    def get_bookings(self):
        return list(self._bookings)

    def get_free_rooms(self, slot):
        check_slot(slot)
        return [room for room in self._rooms if self._is_free(room, slot, gap=DEFAULT_GAP)]

    def get_rooms(self):
        return list(self._rooms)

    def get_gap(self, room):
        self._require_room(room)
        return self._gaps[room]

    def _is_free(self, room, slot, ignore=None, gap=None):
        if gap is None:
            gap = self._gaps[room]
        for other in self._rooms[room]:
            if other == ignore:
                continue
            if abs(self._bookings[other][1] - slot) <= gap:
                return False
        return True

    def _require_free(self, room, slot, ignore=None, gap=None):
        if not self._is_free(room, slot, ignore, gap):
            raise RoomBusy(f"room {room!r} is not free in slot {slot}")

    def _require_room(self, room):
        # Non-str names are never stored, so they count as missing too.
        if not isinstance(room, str) or room not in self._rooms:
            raise KeyError(room)

    def _require_booking(self, booking_id):
        if not isinstance(booking_id, str) or booking_id not in self._bookings:
            raise KeyError(booking_id)
        return self._bookings[booking_id]
