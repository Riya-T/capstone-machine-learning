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
Valid times: `start` is an `int` of 0 or more and `end` is an `int`
greater than `start`. There is no upper limit on times.

## The 10-minute gap

After each meeting the room needs 10 minutes to be tidied up. So a booking
from `start` to `end` keeps its room busy from minute `start` up to, but
not including, minute `end + 10`, and two bookings of the same room clash
when those busy stretches overlap. Bookings in different rooms never clash.

For example, next to a booking from 100 to 160 (busy from 100 up to 170):

| another booking in the same room | result |
|---|---|
| 170 to 200 | allowed: it starts 10 minutes after 160 |
| 169 to 200 | clash: it starts only 9 minutes after 160 |
| 50 to 90 | allowed: it ends 10 minutes before 100 |
| 50 to 91 | clash: it ends only 9 minutes before 100 |
| 120 to 140 | clash: it overlaps |
| 90 to 300 | clash: it overlaps |

`book`, `reschedule` and `get_free_rooms` all use this rule.

## Rooms

- `add_room(room)` adds a room with no bookings. It raises:
  - `ValueError` for an empty name;
  - `BookingError` for a name that was already added.
- `get_rooms()` returns the names of all rooms, in the order they were
  added.

## Bookings

- `book(booking_id, room, start, end)` books the room from `start` to
  `end`. It raises:
  - `KeyError` when the room does not exist;
  - `ValueError` when the booking id is an empty string or `None`, or the
    times are not valid;
  - `BookingError` when the booking id is already used, in any room;
  - `RoomBusy` when the booking clashes with a booking of that room.
- `reschedule(booking_id, start, end)` gives an existing booking new times
  in the same room. It is checked only against the other bookings of its
  room, never against its own old times, so a booking can be moved to
  times that overlap its old ones, or to the same times. It raises:
  - `KeyError` when the booking does not exist;
  - `ValueError` when the times are not valid;
  - `RoomBusy` when the new times clash with another booking of the room.
- `get_booking(booking_id)` returns `(room, start, end)`, with the times
  the booking has now. It raises `KeyError` when the booking does not
  exist.
- `get_room_bookings(room)` returns the ids of the room's bookings sorted
  by their start, earliest first, whatever order they were booked or
  rescheduled in. It raises `KeyError` when the room does not exist.
- `get_free_rooms(start, end)` returns the rooms, in the order they were
  added, where a booking from `start` to `end` could be made right now:
  the rooms where it would not clash with any booking. It raises
  `ValueError` when the times are not valid, just like `book`.
- `reschedule`, `get_booking` and `get_room_bookings` raise `KeyError` also
  for values that are not strings at all, such as `None` or `1`.

`RoomBusy` is raised only when a call has no other problem. Which error is
raised when a call has several other problems (for example a room that
does not exist and invalid times) is unspecified.

A failed call has no effect: if a method raises, every room and booking is
unchanged.

## Example

```python
planner = RoomPlanner()
planner.add_room("oak")
planner.add_room("elm")
planner.book("review", "oak", 600, 660)
planner.book("standup", "oak", 540, 590)  # allowed: it ends 10 minutes before 600
planner.get_room_bookings("oak")          # ["standup", "review"]: earliest start first
planner.book("lunch", "oak", 665, 700)    # RoomBusy: only 5 minutes after 660
planner.get_free_rooms(665, 700)          # ["elm"]
planner.get_free_rooms(670, 700)          # ["oak", "elm"]
planner.reschedule("standup", 700, 730)   # allowed: it starts 40 minutes after 660
planner.get_room_bookings("oak")          # ["review", "standup"]
planner.get_booking("standup")            # ("oak", 700, 730)
planner.reschedule("review", 630, 690)    # allowed: its own old times do not count
planner.reschedule("review", 630, 691)    # RoomBusy: it ends only 9 minutes before 700
planner.get_booking("review")             # ("oak", 630, 690): the failed call changed nothing
planner.get_free_rooms(30, 30)            # ValueError: end is not greater than start
planner.get_booking("lunch")              # KeyError: "lunch" was never booked
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names passed to `add_room` that are not strings, booking ids
passed to `book` that are not strings (other than `None`), `bool` times,
which error a call with several problems raises (other than that
`RoomBusy` comes last), what happens if a returned list is changed, the
text of error messages, saving the planner to a file, and use from several
threads.
