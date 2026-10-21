"""Movie bookings: movies, their showings, and the seats booked for each.

Planted bug (initial version): a showing id that is already used is
accepted again, replacing the old showing and its bookings. The public
checks never reuse an id, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from bookings import BoxOffice
    office = BoxOffice()
    office.add_movie("Dune")
    office.add_showing("d1", "Dune", 600, 40)
    office.book("d1", "ann", 2)
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


class BoxOffice:
    def __init__(self):
        self._movies = []  # titles in the order added
        self._showings = {}  # showing id -> (title, start, seats), in the order added
        self._bookings = {}  # showing id -> list of (customer, seats)

    def add_movie(self, title):
        check_name(title, "title")
        if title in self._movies:
            raise BookingError(f"movie {title!r} was already added")
        self._movies.append(title)

    def add_showing(self, showing_id, title, start, seats):
        check_name(showing_id, "showing_id")
        self._require_movie(title)
        check_count(start, "start", 0)
        check_count(seats, "seats", 1)
        self._showings[showing_id] = (title, start, seats)
        self._bookings[showing_id] = []

    def book(self, showing_id, customer, seats):
        self._require_showing(showing_id)
        check_name(customer, "customer")
        check_count(seats, "seats", 1)
        if seats > self.get_free_seats(showing_id):
            raise NoSeats(f"showing {showing_id!r} has no {seats} free seats")
        self._bookings[showing_id].append((customer, seats))

    def get_free_seats(self, showing_id):
        self._require_showing(showing_id)
        booked = sum(seats for _, seats in self._bookings[showing_id])
        return self._showings[showing_id][2] - booked

    def get_bookings(self, showing_id):
        self._require_showing(showing_id)
        return list(self._bookings[showing_id])

    def get_showings(self, title):
        self._require_movie(title)
        ids = [sid for sid, (t, _, _) in self._showings.items() if t == title]
        # sorted is stable, so equal starts keep the order they were added in.
        return sorted(ids, key=lambda sid: self._showings[sid][1])

    def get_movies(self):
        return list(self._movies)

    def _require_movie(self, title):
        if not isinstance(title, str) or title not in self._movies:
            raise KeyError(title)

    def _require_showing(self, showing_id):
        if not isinstance(showing_id, str) or showing_id not in self._showings:
            raise KeyError(showing_id)
