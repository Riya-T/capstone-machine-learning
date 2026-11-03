Give `pantry.py` a notion of the current day, so that batches past their
use-by day count as expired and can no longer be used.

- Add `Pantry.set_day(day)` and `Pantry.get_day() -> int`. The day starts
  at 0. The new day must be an `int` (not a `bool`) that is not before the
  current day; anything else raises `ValueError` and the day is unchanged.
  Setting the day to the current day is allowed and does nothing.
- A batch is expired when its use-by day is before the current day. A batch
  is still usable on its use-by day itself.
- `use_item` never takes from an expired batch, wherever it is among the
  item's batches. It takes from the batches that are not expired, first in,
  first out as before. If they hold fewer units than requested, it takes
  all they hold and leaves the expired batches as they are, even when those
  hold more. For example, with batches `[(3, 2), (8, 5)]` on day 4,
  `use_item(name, 6)` takes the 5 units of the day-8 batch and leaves
  `[(3, 2), (8, 0)]`.
- Add `Pantry.get_usable_quantity(name) -> int` and
  `Pantry.get_expired_quantity(name) -> int`: how many units of the item
  are left in batches that are not expired, and in batches that are.
  Together they add up to `get_quantity(name)`, which keeps counting every
  batch, and `get_batches` keeps listing every batch.
- Add `Pantry.discard_expired(name) -> int`: throws away all of the item's
  expired batches, including used-up ones, so that `get_batches` no longer
  lists them, and returns how many units were thrown away, 0 if there were
  none. The batches that are left keep their order. Nothing else ever
  removes a batch.
- The three new per-item methods raise `KeyError` for a name that is not an
  item.

All existing behavior must keep working.
