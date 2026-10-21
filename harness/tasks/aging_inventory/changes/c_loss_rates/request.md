The florist now stocks flowers that fade at different speeds. Make the
daily freshness losses in `cooler.py` adjustable, for the whole cooler and
for single batches.

- `FlowerCooler` takes two new keyword arguments, `daily_loss=2` and
  `late_loss=5`: the freshness a batch loses at the end of a day while it
  still has days left, and once it has none. Each must be an `int` of 0 or
  more (not a `bool`); anything else raises `ValueError`.
- `add_batch` takes the same two keyword arguments with a default of
  `None`. `None` means the batch uses the cooler's value; any other value
  must be an `int` of 0 or more (not a `bool`), or `ValueError` is raised
  and no batch is added. The two are independent: a batch may set only one
  of them and use the cooler's value for the other.
- `end_day` uses each batch's own losses. Freshness still never goes
  below 0, and a loss of 0 leaves the freshness unchanged.
- Add `FlowerCooler.get_losses(batch_id) -> tuple[int, int]`, which
  returns the batch's `(daily_loss, late_loss)`.
- Add `FlowerCooler.set_losses(batch_id, daily_loss, late_loss)`, which
  replaces both of the batch's losses from the next `end_day` on. Freshness
  already lost stays lost. It raises `KeyError` for a batch that is not in
  the cooler, then `ValueError` if either value is invalid; in each case
  nothing changes.
- `get_losses` raises `KeyError` for a batch that is not in the cooler.

All existing behavior must keep working.
