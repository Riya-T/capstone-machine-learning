"""Movie bookings with cancellations and movie genres.

Correct solution for movie_bookings after c_cancel and c_genres.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from bookings import BoxOffice
    office = BoxOffice()
    office.add_movie("Dune", genre="scifi")
    office.add_showing("d1", "Dune", 600, 40)
    office.book("d1", "ann", 2)
    office.get_genre_seats_booked("scifi")
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
        self._genres = {}  # title -> genre, in the order the movies were added
        self._showings = {}  # showing id -> (title, start, seats), in the order added
        self._bookings = {}  # showing id -> list of active (customer, seats)
        self._cancelled = {}  # showing id -> list of (customer, seats), in cancel order

    def add_movie(self, title, genre="general"):
        check_name(title, "title")
        check_name(genre, "genre")
        if title in self._genres:
            raise BookingError(f"movie {title!r} was already added")
        self._genres[title] = genre

    def add_showing(self, showing_id, title, start, seats):
        check_name(showing_id, "showing_id")
        if showing_id in self._showings:
            raise BookingError(f"showing {showing_id!r} is already used")
        self._require_movie(title)
        check_count(start, "start", 0)
        check_count(seats, "seats", 1)
        self._showings[showing_id] = (title, start, seats)
        self._bookings[showing_id] = []
        self._cancelled[showing_id] = []

    def book(self, showing_id, customer, seats):
        self._require_showing(showing_id)
        check_name(customer, "customer")
        check_count(seats, "seats", 1)
        if seats > self.get_free_seats(showing_id):
            raise NoSeats(f"showing {showing_id!r} has no {seats} free seats")
        self._bookings[showing_id].append((customer, seats))

    def cancel(self, showing_id, customer):
        self._require_showing(showing_id)
        check_name(customer, "customer")
        bookings = self._bookings[showing_id]
        for index in range(len(bookings) - 1, -1, -1):
            if bookings[index][0] == customer:
                booking = bookings.pop(index)
                self._cancelled[showing_id].append(booking)
                return booking[1]
        raise BookingError(f"{customer!r} has no booking on showing {showing_id!r}")

    def get_free_seats(self, showing_id):
        self._require_showing(showing_id)
        return self._showings[showing_id][2] - self._booked(showing_id)

    def get_bookings(self, showing_id):
        self._require_showing(showing_id)
        return list(self._bookings[showing_id])

    def get_cancelled(self, showing_id):
        self._require_showing(showing_id)
        return list(self._cancelled[showing_id])

    def get_showings(self, title):
        self._require_movie(title)
        ids = [sid for sid, (t, _, _) in self._showings.items() if t == title]
        # sorted is stable, so equal starts keep the order they were added in.
        return sorted(ids, key=lambda sid: self._showings[sid][1])

    def get_movies(self):
        return list(self._genres)

    def get_genre(self, title):
        self._require_movie(title)
        return self._genres[title]

    def get_genres(self):
        return list(dict.fromkeys(self._genres.values()))

    def get_movies_in_genre(self, genre):
        return [title for title, g in self._genres.items() if g == genre]

    def get_genre_seats_booked(self, genre):
        titles = set(self.get_movies_in_genre(genre))
        return sum(
            self._booked(sid) for sid, (title, _, _) in self._showings.items() if title in titles
        )

    def _booked(self, showing_id):
        return sum(seats for _, seats in self._bookings[showing_id])

    def _require_movie(self, title):
        if not isinstance(title, str) or title not in self._genres:
            raise KeyError(title)

    def _require_showing(self, showing_id):
        if not isinstance(showing_id, str) or showing_id not in self._showings:
            raise KeyError(showing_id)
