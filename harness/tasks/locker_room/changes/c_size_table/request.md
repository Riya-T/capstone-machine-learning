Make the sizes and fees in `lockers.py` adjustable, so that each site can
use its own locker sizes and prices, and single lockers can be priced on
their own.

- `LockerRoom` takes a new keyword argument `size_table=None`. `None` means
  the current table (`"small"` 200, `"medium"` 300, `"large"` 500).
  Otherwise it is a `dict` that maps each size name to its fee in cents,
  for example `{"xs": 100, "s": 150, "m": 250, "l": 400, "xl": 600}`.
- The table is valid when it is a non-empty `dict` whose names are
  non-empty strings and whose fees are `int`s of 0 or more.
  Anything else raises `ValueError`.
- The sizes accepted by `add_locker` and `store` are exactly the names in
  the room's table; any other size raises `ValueError` as before. An item
  still goes only into a locker of its own size.
- `add_locker` takes a new keyword argument `fee=None`. `None` means the
  locker charges the fee of its size from the table; anything else must be
  an `int` of 0 or more, or `ValueError` is raised and no locker is added.
  Which error `add_locker` raises when one call has several problems (for
  example an invalid fee and an id that was already added) is unspecified.
- `store` adds the fee of the chosen locker to the takings, which is that
  locker's own fee if it was given one.
- Add `LockerRoom.get_sizes() -> list[str]`: the size names, in the order of
  the table.
- Add `LockerRoom.get_fee(locker_id) -> int`: the fee the locker charges.
  It raises `KeyError` for a locker id that was not added, including values
  that are not strings.

All existing behavior must keep working.
