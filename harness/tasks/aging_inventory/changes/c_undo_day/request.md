Sometimes the florist ends a day by mistake. Let `cooler.py` take back
days that were ended.

- Add `FlowerCooler.undo_day()`. It takes back the most recent `end_day`
  that has not been taken back yet: every batch that day changed gets back
  exactly the freshness and days left it had just before that day. This
  includes a batch that wilted that day. Calling it again takes back the
  day before, and so on.
- If there is no day left to take back, `undo_day` raises `CoolerError`
  and changes nothing.
- `undo_day` only undoes the effect of `end_day`. Batches added or removed
  since then stay added or removed. A batch added after that day is not
  changed by taking it back, even if it reuses the id of a batch that was
  in the cooler on that day.
- Add `FlowerCooler.get_day() -> int`: the number of days ended so far
  minus the number taken back. It starts at 0.
- `end_day` works as before after an `undo_day`.

All existing behavior must keep working.
