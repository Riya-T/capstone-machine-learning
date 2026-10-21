Let customers cancel bookings in `bookings.py`.

- Add `BoxOffice.cancel(showing_id, customer) -> int`. It cancels the
  customer's most recent booking on that showing that is not yet cancelled
  and returns the number of seats it had. Those seats are free again, and
  `get_bookings` no longer lists the booking; the other bookings keep their
  order. Calling `cancel` again cancels the customer's next most recent
  booking, and so on.
- `cancel` raises `KeyError` for a showing id that was not added, then
  `ValueError` for a customer that is not a non-empty string, then
  `BookingError` when the customer has no booking left on that showing. In
  each case nothing changes.
- Add `BoxOffice.get_cancelled(showing_id) -> list[tuple[str, int]]`, which
  returns the showing's cancelled bookings as `(customer, seats)` tuples in
  the order they were cancelled. It raises `KeyError` for a showing id that
  was not added.

All existing behavior must keep working.
