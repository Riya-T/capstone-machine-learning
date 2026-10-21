Give `pantry.py` a notion of the current day, so that batches past their
use-by day count as expired and can no longer be used.

- Add `Pantry.set_day(day)` and `Pantry.get_day() -> int`. The day starts
  at 0. The new day must be an `int` (not a `bool`) that is not before the
  current day; anything else raises `ValueError` and the day is unchanged.
  Setting the day to the current day is allowed and does nothing.
- A batch is expired when its use-by day is before the current day. A batch
  is still usable on its use-by day itself.
- `use_item` takes only from batches that are not expired, earliest use-by
  day first as before. If the item has fewer usable units than requested,
  raise `PantryError` and change nothing, even when the expired batches
  would make up the difference.
- Add `Pantry.get_usable_quantity(name) -> int` and
  `Pantry.get_expired_quantity(name) -> int`: how many units of the item
  are in batches that are not expired, and in batches that are. Together
  they add up to `get_quantity(name)`, which keeps counting every batch,
  and `get_batches` keeps listing every batch.
- Add `Pantry.discard_expired(name) -> int`: throws away the item's expired
  batches and returns how many units were thrown away, 0 if there were
  none.
- The three new per-item methods raise `KeyError` for a name that is not an
  item.

All existing behavior must keep working.
