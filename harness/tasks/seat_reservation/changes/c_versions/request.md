Several booking clerks change bookings in `seats.py` at the same time. Give
every booking a version number so a clerk working from an old view of a
booking is stopped instead of overwriting someone else's change.

- Add `class VersionConflict(ReservationError)` to `seats.py`.
- A booking has version 1 when `reserve` creates it. Every successful
  `move` of it, and every successful `add_seats` to it (below), adds 1 to
  its version. A failed call leaves the version unchanged, and changes to
  other bookings never change it.
- Add `SeatPlanner.get_version(booking_id) -> int`; it raises `KeyError`
  for a booking id that is not booked.
- `move` takes a new keyword argument `expected_version=None`. `None` means
  no check. Otherwise, if it is not equal to the booking's current version,
  `VersionConflict` is raised and nothing changes.
- Add `SeatPlanner.add_seats(booking_id, count, expected_version=None)`,
  which adds `count` passengers to a booking in the coach it is already in.
  They get the lowest-numbered free seats of that coach, and the booking's
  seats are still returned in increasing order by `get_booking`. If the
  coach cannot take `count` more passengers within its limit,
  `NotEnoughSeats` is raised. A count that is not an `int` of at least 1
  raises `ValueError`. `expected_version` works as for `move`.

Which error is raised when one `add_seats` call has several of these
problems, or when a `move` with a wrong `expected_version` also has
another problem (for example a coach without room), is unspecified.

All existing behavior must keep working.
