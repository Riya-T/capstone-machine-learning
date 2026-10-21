Add a service charge to bills in `orders.py`, and keep track of the money
taken over the day.

- `Restaurant` takes a new keyword argument `service_percent=0`: the
  service charge as a whole percentage of what a table ordered. It must be
  an `int` that is 0 or more (not a `bool`); anything else raises
  `ValueError`.
- Add `Restaurant.get_subtotal(table) -> int`: the sum of quantity times
  price over the table's order, which is what `get_bill` returned until
  now.
- Add `Restaurant.get_service_charge(table) -> int`: the subtotal times
  `service_percent`, divided by 100 and rounded down to whole cents.
- `get_bill(table)` now returns the subtotal plus the service charge. With
  the default `service_percent=0` it returns what it always did.
- Add `Restaurant.get_takings() -> int`: the sum of the bills, service
  charge included, of every table closed so far, each closing counting
  once. A table that is closed, opened again and closed again counts for
  both closings. Tables that are still open count for nothing; what a
  table ordered while open never changes the takings until it is closed.
- `get_subtotal` and `get_service_charge` raise `KeyError` for a table that
  is not open.

All existing behavior must keep working.
