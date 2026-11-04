Let bookings in `seats.py` be cancelled, in whole or in part, when
passengers drop out.

- Add `SeatPlanner.cancel(booking_id, count=None)`.
  - With `count=None` the whole booking is cancelled: its passengers no
    longer count for its coach, and the booking id is no longer booked, so
    `get_booking` and `move` raise `KeyError` for it and `reserve` may book
    the same id again.
  - With a count, that many passengers leave the booking, which stays in
    its coach with the others: a booking `("A", 4)` becomes `("A", 3)`
    after `cancel(booking_id, 1)`. A count equal to the booking's size
    cancels the whole booking, exactly as `count=None` does.
  - A count below 1 or above the booking's size raises `ValueError`.
  - `cancel` raises `KeyError` for a booking id that is not booked. Which
    error is raised for a booking id that is not booked together with a
    bad count is unspecified. A failed call changes nothing.
- Room freed by `cancel` is free like any other: later calls to `reserve`
  and `move` can use it.
- Add `SeatPlanner.get_cancelled() -> list[str]`: the ids of every booking
  that was cancelled as a whole, in the order they were cancelled. An id
  that is booked and cancelled twice appears twice. A partial cancel does
  not add the id.

All existing behavior must keep working.
