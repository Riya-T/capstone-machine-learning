# Meeting rooms

Write a module `rooms.py` that books meeting rooms for stretches of time
and keeps a tidy-up gap between one meeting and the next in each room.

## Interface

```python
class BookingError(Exception): ...


class RoomBusy(BookingError): ...


class RoomPlanner:
    def __init__(self): ...
    def add_room(self, room: str) -> None: ...
    def book(self, booking_id: str, room: str, start: int, end: int) -> None: ...
    def reschedule(self, booking_id: str, start: int, end: int) -> None: ...
    def get_booking(self, booking_id: str) -> tuple[str, int, int]: ...
    def get_room_bookings(self, room: str) -> list[str]: ...
    def get_free_rooms(self, start: int, end: int) -> list[str]: ...
    def get_rooms(self) -> list[str]: ...
```

Times are whole minutes, as `int`. A booking from `start` to `end` holds
the room from minute `start` up to, but not including, minute `end`.

## Rooms

- `add_room(room)` adds a room with no bookings. An empty name raises
  `ValueError`, and a name that was already added raises `BookingError`.
- `get_rooms()` returns the names of all rooms, in the order they were
  added.

## Bookings

- `book(booking_id, room, start, end)` books the room. The booking id must
  be a non-empty string, `start` must be an `int` of 0 or more, and `end`
  must be an `int` greater than `start`; anything else raises
  `ValueError`. There is no upper limit on times. A booking id that is
  already used, in any room, raises `BookingError`.
- Two bookings in the same room must not overlap, and there must be at
  least 10 minutes between the end of one and the start of the next. A
  booking that ends at minute 60 leaves the room free for one that starts
  at minute 70 or later. A booking that breaks this rule raises `RoomBusy`.
  Bookings in different rooms never affect each other.
- `reschedule(booking_id, start, end)` gives a booking new times in the
  same room. The times are checked like in `book`. The booking is checked
  against the other bookings of its room with the same rule, but never
  against its own old times, and raises `RoomBusy` if it breaks the rule.
- `get_booking(booking_id)` returns `(room, start, end)`.
- `get_room_bookings(room)` returns the ids of the room's bookings,
  earliest start first.
- `get_free_rooms(start, end)` returns the rooms, in the order they were
  added, where a booking from `start` to `end` could be made right now. The
  times are checked like in `book`.
- Every method that takes a room name or a booking id raises `KeyError`
  when the room or booking does not exist, including values that are not
  strings at all, such as `None` or `1`.

When a call has several problems, the first of these is raised:

1. `KeyError` for a room or booking that does not exist;
2. `ValueError` for an invalid name, booking id or time;
3. `BookingError` for a name or booking id that is already used;
4. `RoomBusy`.

A failed call has no effect: if a method raises, every room and booking is
unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names passed to `add_room` that are not strings, `bool` times,
what happens if a returned list is changed, the text of error messages,
saving the planner to a file, and use from several threads.
