Give `pantry.py` a notion of the current day, so that batches past their
use-by day count as expired and can no longer be used.

- Add `Pantry.set_day(day)` and `Pantry.get_day() -> int`. The day starts
  at 0. The new day must be an `int` that is not before the current day;
  anything else raises `ValueError` and the day is unchanged. Setting the
  day to the current day is allowed and does nothing.
- A batch is expired when its use-by day is before the current day. A batch
  is still usable on its use-by day itself: on day 4, a batch to be used by
  day 4 is usable and one to be used by day 3 is expired.
- `use_item` never takes from an expired batch, wherever it is among the
  item's batches. It takes from the batches that are not expired, first in,
  first out as before. If they hold fewer units than requested, it takes
  all they hold. This is not an error.
- Whether `use_item` also throws away the item's expired batches is up to
  you. After a call to `use_item`, each expired batch of the item is either
  still listed by `get_batches` with all of its units, or gone. Other items
  are not touched. For example, with batches `[(3, 2), (8, 5)]` on day 4,
  `use_item(name, 6)` takes the 5 units of the day-8 batch, and
  `get_batches` then lists the day-3 batch as `(3, 2)` or not at all.
- Add `Pantry.get_usable_quantity(name) -> int` and
  `Pantry.get_expired_quantity(name) -> int`: how many units of the item
  are left in batches that are not expired, and in batches that are.
  Together they add up to `get_quantity(name)`. Until an expired batch is
  thrown away, `get_quantity` keeps counting it and `get_batches` keeps
  listing it.
- Add `Pantry.discard_expired(name) -> int`: throws away all of the item's
  expired batches, so that `get_batches` no longer lists them, and returns
  how many units were thrown away, 0 if there were none. The batches that
  are left keep their order.
- The three new per-item methods raise `KeyError` for a name that is not an
  item.
- A call that raises changes nothing: no batch is used or thrown away.

All existing behavior must keep working.
