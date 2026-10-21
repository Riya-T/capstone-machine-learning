Add occupancy figures to `hotel.py`, so the front desk can see how full
the hotel is.

- Add `Hotel.get_occupancy(night) -> int`: the number of rooms that hold a
  booking on that night. A night that is not an `int` of 1 or more raises
  `ValueError`.
- Add `Hotel.get_nights_booked(room) -> int`: the total number of nights
  booked in that room, over all of its bookings. It raises `KeyError` for a
  room that does not exist.
- Add `Hotel.get_guest_nights(guest) -> int`: the total number of nights
  booked under that guest, over all rooms. A guest with no bookings gives 0;
  no error is raised for a name nobody has used.
- A booking counts whatever its status: a checked-in or checked-out booking
  still holds its nights.

All existing behavior must keep working.
