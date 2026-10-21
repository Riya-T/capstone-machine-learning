Let bookings in `hotel.py` be cancelled before the guest arrives.

- Add `Hotel.cancel(booking_id)`. It raises `KeyError` for an id that is not
  a booking id, then `HotelError` unless the booking's status is `"booked"`
  (a checked-in, checked-out or already cancelled booking cannot be
  cancelled). In each case nothing changes.
- After a successful `cancel`, `get_status(booking_id)` returns
  `"cancelled"`, and `check_in` and `check_out` on that booking raise
  `HotelError` like any other wrong status.
- A cancelled booking no longer holds its nights: `get_guest` returns `None`
  for them, the room can be booked again for those nights, and any count or
  listing that is based on bookings ignores it.
- A cancelled booking keeps its id and that id is never given to another
  booking: the next successful `book` still gets the next unused id.

All existing behavior must keep working.
