Let a table's most recent order be voided in `orders.py`, for example when
a waiter keyed in the wrong dish.

- Add `Restaurant.void_last(table) -> tuple[str, int]`. It cancels the most
  recent call to `order` for that table that has not been voided yet, and
  returns that call's `(dish, quantity)`. Calling it again voids the call
  before that, and so on back to the first.
- Each call to `order` is voided on its own, even when the same dish was
  ordered more than once. For example, after `order("t1", "soup", 1)`,
  `order("t1", "cake", 2)` and `order("t1", "soup", 3)`, `get_order("t1")`
  is `[("soup", 4), ("cake", 2)]`. The first `void_last("t1")` returns
  `("soup", 3)` and leaves `[("soup", 1), ("cake", 2)]`; the next returns
  `("cake", 2)` and leaves `[("soup", 1)]`.
- A voided call no longer counts: `get_order` and `get_bill` behave as if
  it had never been placed. If every order of a dish is voided, the dish
  disappears from `get_order`; if a dish is ordered again afterwards it is
  placed at the end, as a newly ordered dish.
- Add `Restaurant.get_voided(table) -> list[tuple[str, int]]`: the voided
  calls of the table's current sitting as `(dish, quantity)` tuples, one
  per voided call, in the order they were voided. A table opened again
  after closing starts with nothing voided.
- `void_last` raises `KeyError` for a table that is not open, and
  `RestaurantError` for an open table that has no order left to void. In
  each case nothing changes. `get_voided` raises `KeyError` for a table
  that is not open.

All existing behavior must keep working.
