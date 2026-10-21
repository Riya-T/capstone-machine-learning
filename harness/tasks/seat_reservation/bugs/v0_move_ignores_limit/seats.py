"""Seat reservation: groups of passengers booked onto the coaches of a
day-trip operator, never filling a coach beyond 70 % of its seats.

Planted bug (initial version): `move` does not check the new coach's
limit, so a move can fill a coach beyond 70 %. The public checks never
move into a full coach, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from seats import SeatPlanner
    planner = SeatPlanner()
    planner.add_coach("A", 10)
    planner.reserve("smith", 3)      # -> "A", seats [1, 2, 3]
"""


class ReservationError(Exception):
    pass


class NotEnoughSeats(ReservationError):
    pass


FILL_PERCENT = 70  # no coach is filled beyond this share of its seats


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_count(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{what} must be an int >= 1, got {value!r}")


class SeatPlanner:
    def __init__(self):
        self._coaches = {}  # coach id -> number of seats, in the order added
        self._bookings = {}  # booking id -> (coach id, sorted seat numbers)

    def add_coach(self, coach_id, seats):
        check_id(coach_id, "coach_id")
        check_count(seats, "seats")
        if coach_id in self._coaches:
            raise ReservationError(f"coach {coach_id!r} was already added")
        self._coaches[coach_id] = seats

    def reserve(self, booking_id, size):
        check_id(booking_id, "booking_id")
        check_count(size, "size")
        if booking_id in self._bookings:
            raise ReservationError(f"booking {booking_id!r} is already booked")
        for coach_id in self._coaches:
            if size <= self._available(coach_id):
                self._bookings[booking_id] = (coach_id, self._free_seats(coach_id, size))
                return coach_id
        raise NotEnoughSeats(f"no coach can take a group of {size}")

    def move(self, booking_id, coach_id):
        self._require_booking(booking_id)
        self._require_coach(coach_id)
        current, seats = self._bookings[booking_id]
        if current == coach_id:
            raise ValueError(f"booking {booking_id!r} is already in coach {coach_id!r}")
        self._bookings[booking_id] = (coach_id, self._free_seats(coach_id, len(seats)))

    def get_booking(self, booking_id):
        self._require_booking(booking_id)
        coach_id, seats = self._bookings[booking_id]
        return (coach_id, list(seats))

    def get_reserved(self, coach_id):
        self._require_coach(coach_id)
        return self._reserved(coach_id)

    def get_available(self, coach_id):
        self._require_coach(coach_id)
        return self._available(coach_id)

    def get_coaches(self):
        return list(self._coaches)

    # -- helpers --

    def _require_coach(self, coach_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(coach_id, str) or coach_id not in self._coaches:
            raise KeyError(coach_id)

    def _require_booking(self, booking_id):
        if not isinstance(booking_id, str) or booking_id not in self._bookings:
            raise KeyError(booking_id)

    def _limit(self, coach_id):
        return self._coaches[coach_id] * FILL_PERCENT // 100

    def _taken(self, coach_id):
        return {seat for c, seats in self._bookings.values() if c == coach_id for seat in seats}

    def _reserved(self, coach_id):
        return len(self._taken(coach_id))

    def _available(self, coach_id):
        return self._limit(coach_id) - self._reserved(coach_id)

    def _free_seats(self, coach_id, count):
        taken = self._taken(coach_id)
        free = [n for n in range(1, self._coaches[coach_id] + 1) if n not in taken]
        return free[:count]
