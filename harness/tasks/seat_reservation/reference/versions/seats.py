"""Seat reservation with versioned bookings, so a clerk working from an old
view of a booking cannot overwrite a newer change.

Correct solution for seat_reservation after c_versions.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from seats import SeatPlanner
    planner = SeatPlanner()
    planner.add_coach("A", 10)
    planner.reserve("smith", 3)
    planner.add_seats("smith", 1, expected_version=1)
"""


class ReservationError(Exception):
    pass


class NotEnoughSeats(ReservationError):
    pass


class VersionConflict(ReservationError):
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
        # booking id -> {"coach", "seats" (sorted), "version"}
        self._bookings = {}

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
                seats = self._free_seats(coach_id, size)
                self._bookings[booking_id] = {"coach": coach_id, "seats": seats, "version": 1}
                return coach_id
        raise NotEnoughSeats(f"no coach can take a group of {size}")

    def move(self, booking_id, coach_id, expected_version=None):
        self._require_booking(booking_id)
        self._require_coach(coach_id)
        booking = self._bookings[booking_id]
        if booking["coach"] == coach_id:
            raise ValueError(f"booking {booking_id!r} is already in coach {coach_id!r}")
        self._check_version(booking_id, expected_version)
        size = len(booking["seats"])
        if size > self._available(coach_id):
            raise NotEnoughSeats(f"coach {coach_id!r} cannot take {size} more")
        booking["seats"] = self._free_seats(coach_id, size)
        booking["coach"] = coach_id
        booking["version"] += 1

    def add_seats(self, booking_id, count, expected_version=None):
        self._require_booking(booking_id)
        check_count(count, "count")
        self._check_version(booking_id, expected_version)
        booking = self._bookings[booking_id]
        if count > self._available(booking["coach"]):
            raise NotEnoughSeats(f"coach {booking['coach']!r} cannot take {count} more")
        booking["seats"] = sorted(booking["seats"] + self._free_seats(booking["coach"], count))
        booking["version"] += 1

    def get_booking(self, booking_id):
        self._require_booking(booking_id)
        booking = self._bookings[booking_id]
        return (booking["coach"], list(booking["seats"]))

    def get_version(self, booking_id):
        self._require_booking(booking_id)
        return self._bookings[booking_id]["version"]

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

    def _check_version(self, booking_id, expected_version):
        current = self._bookings[booking_id]["version"]
        if expected_version is not None and expected_version != current:
            raise VersionConflict(
                f"booking {booking_id!r} is at version {current}, not {expected_version!r}"
            )

    def _limit(self, coach_id):
        return self._coaches[coach_id] * FILL_PERCENT // 100

    def _taken(self, coach_id):
        return {
            seat
            for booking in self._bookings.values()
            if booking["coach"] == coach_id
            for seat in booking["seats"]
        }

    def _reserved(self, coach_id):
        return len(self._taken(coach_id))

    def _available(self, coach_id):
        return self._limit(coach_id) - self._reserved(coach_id)

    def _free_seats(self, coach_id, count):
        taken = self._taken(coach_id)
        free = [n for n in range(1, self._coaches[coach_id] + 1) if n not in taken]
        return free[:count]
