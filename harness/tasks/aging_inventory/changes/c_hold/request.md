Let the florist put batches of `cooler.py` on hold, for example while they
sit in the deep-chill drawer, where they do not age at all.

- Add `FlowerCooler.hold(batch_id)`, `FlowerCooler.release(batch_id)` and
  `FlowerCooler.is_held(batch_id) -> bool`. All three raise `KeyError` for
  a batch that is not in the cooler. New batches are not held. Holding a
  held batch, or releasing one that is not held, does nothing.
- While a batch is held, `end_day` changes neither its freshness nor its
  days left. Once released, it ages again from the values it had when it
  was put on hold.
- A held batch cannot be removed: `remove_batch` raises
  `class BatchHeld(CoolerError)` (add it to `cooler.py`) and changes
  nothing. `KeyError` for an unknown batch comes first.
- Held batches are still listed by `get_batches` and, when their
  freshness is 0, by `get_wilted`.
- Add `FlowerCooler.get_held() -> list[str]`: the ids of the held batches,
  in the order they were added to the cooler.
- Add `FlowerCooler.hold_category(name)`, which holds every batch that is
  in that category now. Batches added to the category later are not held.
  It raises `KeyError` for a category that was never added.
- A batch id that is removed and added again is a new batch, and is not
  held.

All existing behavior must keep working.
