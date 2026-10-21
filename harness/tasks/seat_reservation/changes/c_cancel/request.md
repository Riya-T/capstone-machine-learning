Let bookings in `seats.py` be cancelled, in whole or in part, when
passengers drop out.

- Add `SeatPlanner.cancel(booking_id, count=None)`.
  - With `count=None` the whole booking is cancelled: its seats become free
    and the booking id is no longer booked, so `get_booking` and `move`
    raise `KeyError` for it and `reserve` may book the same id again.
  - With an `int` count, that many passengers leave the booking: its
    `count` highest-numbered seats become free and it keeps the others. A
    count equal to the booking's size cancels the whole booking, exactly as
    `count=None` does.
  - A count that is not an `int` from 1 to the booking's size (not a
    `bool`) raises `ValueError`.
  - `cancel` raises `KeyError` for a booking id that is not booked, before
    any `ValueError`. A failed call changes nothing.
- Seats freed by `cancel` are free like any other: later calls to
  `reserve` and `move` use them, lowest-numbered first.
- Add `SeatPlanner.get_cancelled() -> list[str]`: the ids of every booking
  that was cancelled as a whole, in the order they were cancelled. An id
  that is booked and cancelled twice appears twice. A partial cancel does
  not add the id.

All existing behavior must keep working.
