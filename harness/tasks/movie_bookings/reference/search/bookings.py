"""Movie bookings with search over showings and a customer's bookings.

Correct solution for movie_bookings after c_search. Bookings are kept in one
log so a customer's bookings keep their order across showings.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from bookings import BoxOffice
    office = BoxOffice()
    office.add_movie("Dune")
    office.add_showing("d1", "Dune", 600, 40)
    office.find_showings(title="Dune", earliest=540)
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
        self._log = []  # every booking as (showing id, customer, seats), oldest first

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
        self._log.append((showing_id, customer, seats))

    def get_free_seats(self, showing_id):
        self._require_showing(showing_id)
        booked = sum(seats for sid, _, seats in self._log if sid == showing_id)
        return self._showings[showing_id][2] - booked

    def get_bookings(self, showing_id):
        self._require_showing(showing_id)
        return [(customer, seats) for sid, customer, seats in self._log if sid == showing_id]

    def get_showings(self, title):
        self._require_movie(title)
        return self.find_showings(title=title)

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
        return [(sid, seats) for sid, c, seats in self._log if c == customer]

    def _require_movie(self, title):
        if not isinstance(title, str) or title not in self._movies:
            raise KeyError(title)

    def _require_showing(self, showing_id):
        if not isinstance(showing_id, str) or showing_id not in self._showings:
            raise KeyError(showing_id)
