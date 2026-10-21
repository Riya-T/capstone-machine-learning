# Seat reservation

Write a module `seats.py` that books groups of passengers onto the coaches
(buses) of a day-trip operator. A group always travels together in one
coach, and no coach is filled beyond 70 % of its seats, so late walk-ups
can still get on.

## Interface

```python
class ReservationError(Exception): ...


class NotEnoughSeats(ReservationError): ...


class SeatPlanner:
    def __init__(self): ...
    def add_coach(self, coach_id: str, seats: int) -> None: ...
    def reserve(self, booking_id: str, size: int) -> str: ...
    def move(self, booking_id: str, coach_id: str) -> None: ...
    def get_booking(self, booking_id: str) -> tuple[str, list[int]]: ...
    def get_reserved(self, coach_id: str) -> int: ...
    def get_available(self, coach_id: str) -> int: ...
    def get_coaches(self) -> list[str]: ...
```

## Coaches

- `add_coach(coach_id, seats)` adds a coach whose seats are numbered 1 to
  `seats`. An empty id raises `ValueError`, and so does a number of seats
  that is not an `int` of at least 1. Adding an id that was already added
  raises `ReservationError`.
- A coach's **limit** is `seats * 7 // 10` (70 %, rounded down): a coach
  with 10 seats takes at most 7 passengers, one with 15 seats at most 10,
  and one with 1 seat none at all.
- `get_reserved(coach_id)` returns how many of the coach's seats are
  booked. `get_available(coach_id)` returns how many more passengers it
  can take: its limit minus its reserved seats.
- `get_coaches()` returns the coach ids in the order they were added.

## Bookings

- `reserve(booking_id, size)` books a group of `size` passengers. An empty
  booking id raises `ValueError`, and so does a size that is not an `int`
  of at least 1. A booking id that is already booked raises
  `ReservationError`.
- The group goes into the **first coach, in the order coaches were added,
  that can take the whole group** without going over its limit. It gets the
  `size` lowest-numbered seats of that coach that are free. `reserve`
  returns the id of that coach. If no coach can take the whole group,
  `NotEnoughSeats` is raised.
- `move(booking_id, coach_id)` moves a whole booking to another coach. Its
  old seats become free, and it gets the lowest-numbered free seats of the
  new coach. Moving a booking to the coach it is already in raises
  `ValueError`; a coach that cannot take the whole group within its limit
  raises `NotEnoughSeats`.
- Free seats are not always at the end: after a move, a later booking may
  get seats such as `[1, 2, 6]`.
- `get_booking(booking_id)` returns `(coach_id, seat_numbers)`, with the
  seat numbers in increasing order.
- Every method raises `KeyError` when given a coach id that was not added
  or a booking id that is not booked (except `add_coach` and `reserve`,
  which create them), including values that are not strings, such as
  `None` or `1`.

When a call has several problems, the first of these is raised:

1. for `reserve`: `ValueError` for an invalid booking id or size, then
   `ReservationError` for a booking id that is already booked, then
   `NotEnoughSeats`;
2. for `move`: `KeyError` for the booking, then `KeyError` for the coach,
   then `ValueError` for the same coach, then `NotEnoughSeats`;
3. for `add_coach`: `ValueError` for an invalid id or number of seats,
   then `ReservationError`.

A failed call has no effect: if a method raises, every booking and every
coach is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` sizes or seat counts, ids that are not strings passed to
`add_coach` or `reserve`, what happens if a returned list is changed, the
text of error messages, saving the planner to a file, and use from several
threads.
