Make the sizes and fees in `lockers.py` adjustable, so that each site can
use its own locker sizes and prices, and single lockers can be priced on
their own.

- `LockerRoom` takes a new keyword argument `size_table=None`. `None` means
  the current table (`"small"` 200, `"medium"` 300, `"large"` 500).
  Otherwise it is a `dict` that maps each size name to its fee in cents,
  listed from the smallest size to the largest, for example
  `{"xs": 100, "s": 150, "m": 250, "l": 400, "xl": 600}`.
- The table is valid when it is a non-empty `dict` whose names are
  non-empty strings and whose fees are `int`s of 0 or more (not `bool`s).
  Anything else raises `ValueError`. Fees do not have to grow with the size.
- The sizes accepted by `add_locker` and `store` are exactly the names in
  the room's table; any other size raises `ValueError` as before. An item
  fits into a locker of its own size or of any size listed after it, and
  `store` picks the earliest-listed size that fits and has a free locker,
  as before.
- `add_locker` takes a new keyword argument `fee=None`. `None` means the
  locker charges the fee of its size from the table; anything else must be
  an `int` of 0 or more (not a `bool`), or `ValueError` is raised and no
  locker is added. The `ValueError` checks of `add_locker` come before the
  `LockerError` for an id that was already added; if several values are
  invalid, any of their `ValueError`s may come first.
- `store` adds the fee of the chosen locker to the takings, which is that
  locker's own fee if it was given one.
- Add `LockerRoom.get_sizes() -> list[str]`: the size names, smallest first.
- Add `LockerRoom.get_fee(locker_id) -> int`: the fee the locker charges.
  It raises `KeyError` for a locker id that was not added, including values
  that are not strings.

All existing behavior must keep working.
