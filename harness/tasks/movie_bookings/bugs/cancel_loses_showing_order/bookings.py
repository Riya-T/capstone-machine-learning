"""Movie bookings with search and cancellations.

Planted bug (after c_search and c_cancel): cancellations work, but while
restructuring the bookings get_showings was rewritten without the sort by
start time, so it lists a movie's showings in the order they were added.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from bookings import BoxOffice
    office = BoxOffice()
    office.add_movie("Dune")
    office.add_showing("d1", "Dune", 600, 40)
    office.book("d1", "ann", 2)
    office.cancel("d1", "ann")
"""


class BookingError(Exception):
    pass


class NoSeats(BookingError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_count(value, what, minimum):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{what} must be an int >= {minimum}, got {value!r}")


class Booking:
    def __init__(self, showing_id, customer, seats):
        self.showing_id = showing_id
        self.customer = customer
        self.seats = seats
        self.cancelled = False


class BoxOffice:
    def __init__(self):
        self._movies = []  # titles in the order added
        self._showings = {}  # showing id -> (title, start, seats), in the order added
        self._log = []  # every Booking ever made, oldest first
        self._cancelled = []  # Bookings in the order they were cancelled

    def add_movie(self, title):
        check_name(title, "title")
        if title in self._movies:
            raise BookingError(f"movie {title!r} was already added")
        self._movies.append(title)

    def add_showing(self, showing_id, title, start, seats):
        check_name(showing_id, "showing_id")
        if showing_id in self._showings:
            raise BookingError(f"showing {showing_id!r} is already used")
        self._require_movie(title)
        check_count(start, "start", 0)
        check_count(seats, "seats", 1)
        self._showings[showing_id] = (title, start, seats)

    def book(self, showing_id, customer, seats):
        self._require_showing(showing_id)
        check_name(customer, "customer")
        check_count(seats, "seats", 1)
        if seats > self.get_free_seats(showing_id):
            raise NoSeats(f"showing {showing_id!r} has no {seats} free seats")
        self._log.append(Booking(showing_id, customer, seats))

    def cancel(self, showing_id, customer):
        self._require_showing(showing_id)
        check_name(customer, "customer")
        for booking in reversed(self._active(showing_id)):
            if booking.customer == customer:
                booking.cancelled = True
                self._cancelled.append(booking)
                return booking.seats
        raise BookingError(f"{customer!r} has no booking on showing {showing_id!r}")

    def get_free_seats(self, showing_id):
        self._require_showing(showing_id)
        booked = sum(b.seats for b in self._active(showing_id))
        return self._showings[showing_id][2] - booked

    def get_bookings(self, showing_id):
        self._require_showing(showing_id)
        return [(b.customer, b.seats) for b in self._active(showing_id)]

    def get_cancelled(self, showing_id):
        self._require_showing(showing_id)
        return [(b.customer, b.seats) for b in self._cancelled if b.showing_id == showing_id]

    def get_showings(self, title):
        self._require_movie(title)
        return [sid for sid, (t, _, _) in self._showings.items() if t == title]

    def get_movies(self):
        return list(self._movies)

    def find_showings(self, title=None, earliest=None, latest=None):
        if title is not None:
            self._require_movie(title)
        if earliest is not None:
            check_count(earliest, "earliest", 0)
        if latest is not None:
            check_count(latest, "latest", 0)
        if earliest is not None and latest is not None and earliest > latest:
            raise ValueError("earliest must not be greater than latest")
        found = [
            sid
            for sid, (t, start, _) in self._showings.items()
            if (title is None or t == title)
            and (earliest is None or start >= earliest)
            and (latest is None or start <= latest)
        ]
        # sorted is stable, so equal starts keep the order they were added in.
        return sorted(found, key=lambda sid: self._showings[sid][1])

    def find_customer_bookings(self, customer):
        check_name(customer, "customer")
        return [
            (b.showing_id, b.seats) for b in self._log if b.customer == customer and not b.cancelled
        ]

    def _active(self, showing_id):
        return [b for b in self._log if b.showing_id == showing_id and not b.cancelled]

    def _require_movie(self, title):
        if not isinstance(title, str) or title not in self._movies:
            raise KeyError(title)

    def _require_showing(self, showing_id):
        if not isinstance(showing_id, str) or showing_id not in self._showings:
            raise KeyError(showing_id)
