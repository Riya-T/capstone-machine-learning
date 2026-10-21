"""Seat reservation with adjustable fill percentages, cancellations and
coach groups.

Correct solution for seat_reservation after c_fill_percent, c_cancel and
c_coach_groups.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from seats import SeatPlanner
    planner = SeatPlanner(fill_percent=80)
    planner.add_coach("A", 10, group="comfort")
    planner.reserve("smith", 3, group="comfort")
    planner.cancel("smith", 1)
"""


class ReservationError(Exception):
    pass


class NotEnoughSeats(ReservationError):
    pass


DEFAULT_FILL_PERCENT = 70  # no coach is filled beyond this share of its seats
DEFAULT_GROUP = "standard"


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_count(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{what} must be an int >= 1, got {value!r}")


def check_percent(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
        raise ValueError(f"fill_percent must be an int from 1 to 100, got {value!r}")


class SeatPlanner:
    def __init__(self, fill_percent=DEFAULT_FILL_PERCENT):
        check_percent(fill_percent)
        self._fill_percent = fill_percent
        self._coaches = {}  # coach id -> {"seats", "percent", "group"}, in the order added
        self._bookings = {}  # booking id -> (coach id, sorted seat numbers)
        self._cancelled = []  # ids of whole bookings cancelled, oldest first

    def add_coach(self, coach_id, seats, fill_percent=None, group=DEFAULT_GROUP):
        check_id(coach_id, "coach_id")
        check_count(seats, "seats")
        if fill_percent is None:
            fill_percent = self._fill_percent
        check_percent(fill_percent)
        check_id(group, "group")
        if coach_id in self._coaches:
            raise ReservationError(f"coach {coach_id!r} was already added")
        self._coaches[coach_id] = {"seats": seats, "percent": fill_percent, "group": group}

    def reserve(self, booking_id, size, group=None):
        check_id(booking_id, "booking_id")
        check_count(size, "size")
        candidates = self._coaches_in(group)
        if booking_id in self._bookings:
            raise ReservationError(f"booking {booking_id!r} is already booked")
        for coach_id in candidates:
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
        if len(seats) > self._available(coach_id):
            raise NotEnoughSeats(f"coach {coach_id!r} cannot take {len(seats)} more")
        self._bookings[booking_id] = (coach_id, self._free_seats(coach_id, len(seats)))

    def cancel(self, booking_id, count=None):
        self._require_booking(booking_id)
        coach_id, seats = self._bookings[booking_id]
        if count is None:
            count = len(seats)
        check_count(count, "count")
        if count > len(seats):
            raise ValueError(f"booking {booking_id!r} has only {len(seats)} seats")
        if count == len(seats):
            del self._bookings[booking_id]
            self._cancelled.append(booking_id)
        else:
            self._bookings[booking_id] = (coach_id, seats[: len(seats) - count])

    def get_booking(self, booking_id):
        self._require_booking(booking_id)
        coach_id, seats = self._bookings[booking_id]
        return (coach_id, list(seats))

    def get_cancelled(self):
        return list(self._cancelled)

    def get_reserved(self, coach_id):
        self._require_coach(coach_id)
        return self._reserved(coach_id)

    def get_available(self, coach_id):
        self._require_coach(coach_id)
        return self._available(coach_id)

    def get_coaches(self, group=None):
        return self._coaches_in(group)

    def get_group(self, coach_id):
        self._require_coach(coach_id)
        return self._coaches[coach_id]["group"]

    def get_groups(self):
        groups = []
        for coach in self._coaches.values():
            if coach["group"] not in groups:
                groups.append(coach["group"])
        return groups

    def get_group_available(self, group):
        self._require_group(group)
        return sum(self._available(c) for c in self._coaches_in(group))

    def get_fill_percent(self, coach_id):
        self._require_coach(coach_id)
        return self._coaches[coach_id]["percent"]

    def set_fill_percent(self, coach_id, fill_percent):
        self._require_coach(coach_id)
        check_percent(fill_percent)
        if self._reserved(coach_id) > self._limit_for(coach_id, fill_percent):
            raise ReservationError(f"coach {coach_id!r} already holds more than that")
        self._coaches[coach_id]["percent"] = fill_percent

    # -- helpers --

    def _require_coach(self, coach_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(coach_id, str) or coach_id not in self._coaches:
            raise KeyError(coach_id)

    def _require_booking(self, booking_id):
        if not isinstance(booking_id, str) or booking_id not in self._bookings:
            raise KeyError(booking_id)

    def _require_group(self, group):
        if group not in self.get_groups():
            raise KeyError(group)

    def _coaches_in(self, group):
        if group is None:
            return list(self._coaches)
        self._require_group(group)
        return [c for c, coach in self._coaches.items() if coach["group"] == group]

    def _limit_for(self, coach_id, percent):
        return self._coaches[coach_id]["seats"] * percent // 100

    def _limit(self, coach_id):
        return self._limit_for(coach_id, self._coaches[coach_id]["percent"])

    def _taken(self, coach_id):
        return {seat for c, seats in self._bookings.values() if c == coach_id for seat in seats}

    def _reserved(self, coach_id):
        return len(self._taken(coach_id))

    def _available(self, coach_id):
        return self._limit(coach_id) - self._reserved(coach_id)

    def _free_seats(self, coach_id, count):
        taken = self._taken(coach_id)
        free = [n for n in range(1, self._coaches[coach_id]["seats"] + 1) if n not in taken]
        return free[:count]
