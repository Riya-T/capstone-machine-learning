# Seat reservation

Write a module `seats.py` that books groups of passengers onto the coaches
(buses) of a day-trip operator. A group always travels together in one
coach, and no coach is filled beyond 70 % of its seats, so late walk-ups
can still get on. Seats are not numbered: a booking only says which coach
the group is in and how many passengers it has.

## Interface

```python
class ReservationError(Exception): ...


class NotEnoughSeats(ReservationError): ...


class SeatPlanner:
    def __init__(self): ...
    def add_coach(self, coach_id: str, seats: int) -> None: ...
    def reserve(self, booking_id: str, size: int) -> str: ...
    def move(self, booking_id: str, coach_id: str) -> None: ...
    def get_booking(self, booking_id: str) -> tuple[str, int]: ...
    def get_reserved(self, coach_id: str) -> int: ...
    def get_available(self, coach_id: str) -> int: ...
    def get_coaches(self) -> list[str]: ...
```

## Coaches

- `add_coach(coach_id, seats)` adds a coach with `seats` seats.
  - An empty id raises `ValueError`.
  - A number of seats of 0 or less raises `ValueError`.
  - An id that was already added raises `ReservationError`.
- A coach's **limit** is `seats * 7 // 10` (70 %, rounded down): a coach
  with 10 seats takes at most 7 passengers, one with 15 seats at most 10,
  and one with 1 seat none at all.
- `get_reserved(coach_id)` returns how many passengers are booked into the
  coach: the sum of the sizes of its bookings.
- `get_available(coach_id)` returns how many more passengers it can take:
  its limit minus its reserved seats.
- `get_coaches()` returns the coach ids in the order they were added.

## Bookings

- `reserve(booking_id, size)` books a group of `size` passengers.
  - The group goes into the **first coach, in the order coaches were
    added, that can take the whole group** without going over its limit.
    `reserve` returns the id of that coach.
  - An empty booking id raises `ValueError`.
  - A size of 0 or less raises `ValueError`.
  - A booking id that is already booked raises `ReservationError`.
  - If no coach can take the whole group, `NotEnoughSeats` is raised. A
    group is never split between coaches.
- `move(booking_id, coach_id)` moves a whole booking to another coach. Its
  passengers no longer count for the old coach, and count for the new one.
  - Moving a booking to the coach it is already in raises `ValueError`.
  - A coach that cannot take the whole group within its limit raises
    `NotEnoughSeats`.
- `get_booking(booking_id)` returns `(coach_id, size)`: the coach the
  booking is in and how many passengers it has.

Every method raises `KeyError` when given a coach id that was not added or
a booking id that is not booked (except `add_coach` and `reserve`, which
create them), including values that are not strings, such as `None` or
`1`.

A failed call has no effect: if a method raises, every booking and every
coach is unchanged.

For example:

```python
planner = SeatPlanner()
planner.add_coach("A", 10)     # limit 7
planner.add_coach("B", 20)     # limit 14

planner.reserve("smith", 2)    # "A"
planner.reserve("jones", 3)    # "A"
planner.get_booking("jones")   # ("A", 3)
planner.get_reserved("A")      # 5
planner.get_available("A")     # 2

planner.reserve("brown", 4)    # "B": A has room for only 2 more
planner.get_booking("brown")   # ("B", 4)

planner.move("smith", "B")
planner.get_booking("smith")   # ("B", 2)
planner.get_reserved("A")      # 3
planner.get_reserved("B")      # 6

planner.reserve("green", 4)    # "A": it has room for 4 again
planner.get_available("A")     # 0
planner.move("brown", "A")     # NotEnoughSeats: A is full
planner.reserve("white", 9)    # NotEnoughSeats: A is full, B has room for 8
planner.reserve("white", 8)    # "B"
planner.get_available("B")     # 0
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when one call has several problems, sizes or
seat counts that are not `int`s (such as `2.5`, `"4"` or `None`; 0 and
negative numbers are tested), `bool` values, ids that are not strings passed
to `add_coach` or `reserve`, what happens if a returned list is changed,
the text of error messages, saving the planner to a file, and use from
several threads.
