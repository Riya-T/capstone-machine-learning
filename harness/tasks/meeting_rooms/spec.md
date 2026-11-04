# Meeting rooms

Write a module `rooms.py` that books meeting rooms by the slot.

## Interface

```python
class BookingError(Exception): ...


class RoomBusy(BookingError): ...


class RoomPlanner:
    def __init__(self): ...
    def add_room(self, room: str) -> None: ...
    def book(self, booking_id: str, room: str, slot: int) -> None: ...
    def get_booking(self, booking_id: str) -> tuple[str, int]: ...
    def get_bookings(self) -> list[str]: ...
    def get_free_rooms(self, slot: int) -> list[str]: ...
    def get_rooms(self) -> list[str]: ...
```

The day is cut into numbered slots, as `int`s: slot 0, slot 1, slot 2 and
so on, with no upper limit. Each booking takes one slot of one room.

## One meeting per slot

A room holds one meeting per slot: two bookings of the same room clash when
they are in the same slot. Bookings in neighbouring slots of a room do not
clash, and bookings in different rooms never clash.

## Rooms

- `add_room(room)` adds a room with no bookings. It raises:
  - `ValueError` for an empty name;
  - `BookingError` for a name that was already added.
- `get_rooms()` returns the names of all rooms, in the order they were
  added.

## Bookings

- `book(booking_id, room, slot)` books the room for that slot. It raises:
  - `KeyError` when the room does not exist;
  - `ValueError` when the booking id is an empty string or `None`;
  - `ValueError` when the slot is below 0;
  - `BookingError` when the booking id is already used, in any room;
  - `RoomBusy` when the room already has a booking in that slot.
- `get_booking(booking_id)` returns `(room, slot)`. It raises `KeyError`
  when the booking does not exist, including for values that are not
  strings at all, such as `None` or `1`.
- `get_bookings()` returns the ids of all bookings, in every room, each
  once, in any order.
- `get_free_rooms(slot)` returns the rooms, in the order they were added,
  that have no booking in that slot. It raises `ValueError` when the slot
  is below 0, just like `book`.

A failed call has no effect: if a method raises, every room and booking is
unchanged, and the booking id is not used up.

## Example

```python
planner = RoomPlanner()
planner.add_room("oak")
planner.add_room("elm")
planner.book("review", "oak", 10)
planner.book("standup", "oak", 9)   # allowed: back to back with "review"
planner.book("lunch", "oak", 11)    # allowed: back to back on the other side
planner.book("party", "oak", 10)    # RoomBusy: "oak" is booked in slot 10
planner.get_free_rooms(10)          # ["elm"]
planner.get_free_rooms(12)          # ["oak", "elm"]
planner.book("party", "elm", 10)    # allowed: another room
planner.get_booking("party")        # ("elm", 10)
planner.get_bookings()              # "review", "standup", "lunch" and "party", in any order
planner.get_free_rooms(-1)          # ValueError: the slot is below 0
planner.get_booking("dinner")       # KeyError: "dinner" was never booked
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes the order of `get_bookings`, slots that are not `int`s (such as
`1.5`, `"3"` or `None`), `bool` slots, names passed to `add_room` that are
not strings, booking ids passed to `book` that are not strings (other than
`None`), which error a call with several problems raises (for example a
room that does not exist and a slot below 0), what happens if a returned
list is changed, the text of error messages, saving the planner to a file,
and use from several threads.
