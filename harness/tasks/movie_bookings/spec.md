# Movie bookings

Write a module `bookings.py` that keeps the movies a cinema shows, the
showings of each movie, and the seats customers have booked for them.

## Interface

```python
class BookingError(Exception): ...


class NoSeats(BookingError): ...


class BoxOffice:
    def __init__(self): ...
    def add_movie(self, title: str) -> None: ...
    def add_showing(self, showing_id: str, title: str, start: int, seats: int) -> None: ...
    def book(self, showing_id: str, customer: str, seats: int) -> None: ...
    def get_free_seats(self, showing_id: str) -> int: ...
    def get_bookings(self, showing_id: str) -> list[tuple[str, int]]: ...
    def get_showings(self, title: str) -> list[str]: ...
    def get_movies(self) -> list[str]: ...
```

Start times are minutes after midnight and seat counts are counts, both as
`int`.

## Movies

- `add_movie(title)` adds a movie. An empty title raises `ValueError`, and a
  title that was already added raises `BookingError`.
- `get_movies()` returns the titles in the order they were added.
- `add_showing` and `get_showings` raise `KeyError` for a title that was not
  added, including values that are not strings at all, such as `None`.

## Showings

- `add_showing(showing_id, title, start, seats)` adds a showing of the movie
  `title` that starts `start` minutes after midnight and has `seats` seats.
  An empty showing id raises `ValueError`, and a showing id that is already
  used raises `BookingError`. `start` must be an `int` that is 0 or more and
  `seats` an `int` greater than 0, or `ValueError` is raised.
- `get_showings(title)` returns the ids of the movie's showings, earliest
  start first. Showings with the same start keep the order they were added
  in. A movie with no showings gives an empty list.
- `book`, `get_free_seats` and `get_bookings` raise `KeyError` for a showing
  id that was not added, including values that are not strings at all.

When `add_showing` has several problems, the first of these is raised:

1. `ValueError` for an empty showing id;
2. `BookingError` for a showing id that is already used;
3. `KeyError` for a title that was not added;
4. `ValueError` for an invalid start;
5. `ValueError` for an invalid seat count.

## Bookings

- `book(showing_id, customer, seats)` books `seats` seats of the showing for
  `customer`. The customer must be a non-empty string and the seat count an
  `int` greater than 0, or `ValueError` is raised. Booking more seats than
  are free raises `NoSeats`. The same customer may book the same showing
  several times.
- `get_free_seats(showing_id)` returns the number of seats of the showing
  that are not booked.
- `get_bookings(showing_id)` returns the showing's bookings in the order they
  were made, as `(customer, seats)` tuples, one tuple per call to `book`.

When `book` has several problems, the first of these is raised:

1. `KeyError` for a showing id that was not added;
2. `ValueError` for an invalid customer;
3. `ValueError` for an invalid seat count;
4. `NoSeats`.

A failed call has no effect: if a method raises, every movie, showing and
booking is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes titles and showing ids that are not strings passed to `add_movie`
and `add_showing`, `bool` values for `start` and `seats`, an upper bound on
`start`, what happens if a returned list is changed, the text of error
messages, saving the box office to a file, and use from several threads.
