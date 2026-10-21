Let a table's most recent order be voided in `orders.py`, for example when
a waiter keyed in the wrong dish.

- Add `Restaurant.void_last(table) -> tuple[str, int]`. It cancels the most
  recent call to `order` for that table that has not been voided yet, and
  returns that call's `(dish, quantity)`. Calling it again voids the call
  before that, and so on back to the first.
- A voided call no longer counts: `get_order` and `get_bill` behave as if
  it had never been placed. If every order of a dish is voided, the dish
  disappears from `get_order`; if a dish is ordered again afterwards it is
  placed at the end, as a newly ordered dish.
- Add `Restaurant.get_voided(table) -> list[tuple[str, int]]`: the voided
  calls of the table's current sitting as `(dish, quantity)` tuples, one
  per voided call, in the order they were voided. A table opened again
  after closing starts with nothing voided.
- `void_last` raises `KeyError` for a table that is not open, then
  `RestaurantError` when the table has no order left to void. In each case
  nothing changes. `get_voided` raises `KeyError` for a table that is not
  open.

All existing behavior must keep working.
