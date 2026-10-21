# Hotel rooms

Write a module `hotel.py` that keeps the rooms of a hotel, the bookings made
for them, and whether each guest has checked in or out.

## Interface

```python
class HotelError(Exception): ...


class RoomUnavailable(HotelError): ...


class Hotel:
    def __init__(self): ...
    def add_room(self, room: str) -> None: ...
    def book(self, room: str, guest: str, first_night: int, last_night: int) -> int: ...
    def check_in(self, booking_id: int) -> None: ...
    def check_out(self, booking_id: int) -> None: ...
    def get_status(self, booking_id: int) -> str: ...
    def get_guest(self, room: str, night: int) -> str | None: ...
    def get_rooms(self) -> list[str]: ...
```

Nights are numbered with `int`s starting at 1 (night 1, night 2, ...). There
are no dates.

## Rooms

- `add_room(room)` adds a room with no bookings. An empty name raises
  `ValueError`, and adding a name that is already a room raises `HotelError`.
- `get_rooms()` returns the names of all rooms, in the order they were added.
- `book` and `get_guest` raise `KeyError` when given a room name that is not a
  room, including values that are not strings at all, such as `None` or `1`.

## Bookings

- `book(room, guest, first_night, last_night)` books the room for the guest
  for every night from `first_night` to `last_night`, both included, and
  returns the booking's id. The first successful booking gets id 1, the next
  one id 2, and so on; a failed call uses up no id.
- The guest must be a non-empty string, or `ValueError` is raised.
- Both nights must be `int`s that are 1 or more, and `last_night` must not be
  before `first_night`, or `ValueError` is raised. A booking for a single
  night has `first_night == last_night`.
- A room holds one booking per night. If any night of the range is already
  part of a booking for that room, `RoomUnavailable` is raised. A booking
  that ends on night 3 and one that starts on night 4 do not overlap.
- `get_guest(room, night)` returns the guest whose booking covers that room on
  that night, or `None` if no booking does. A night that is not an `int` of 1
  or more raises `ValueError`.

When a call to `book` has several problems, the first of these is raised:

1. `KeyError` for a room that does not exist;
2. `ValueError` for an invalid guest;
3. `ValueError` for invalid nights;
4. `RoomUnavailable`.

## Checking in and out

Every booking has a status, returned by `get_status(booking_id)`:

- `"booked"` right after `book`;
- `"checked_in"` after `check_in(booking_id)`, which is only allowed while
  the status is `"booked"`;
- `"checked_out"` after `check_out(booking_id)`, which is only allowed while
  the status is `"checked_in"`.

`check_in` or `check_out` in any other status raises `HotelError`. A booking
keeps its nights whatever its status: checking out does not free them.
`check_in`, `check_out` and `get_status` raise `KeyError` for an id that is
not a booking id, including values such as `None` or `"1"`.

A failed call has no effect: if a method raises, every room, booking and
status is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes room names that are not strings passed to `add_room`, `bool` nights,
what happens if a returned list is changed, the text of error messages,
saving the hotel to a file, and use from several threads.
