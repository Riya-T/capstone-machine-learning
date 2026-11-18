Let each hold in `ship.py` have a capacity: the most crates it can take,
counting every cargo type together.

- `add_hold(name, capacity=None)` takes an optional capacity. `None` (the
  default) means the hold has no limit. Otherwise the capacity must be an
  `int` greater than 0; anything else raises `ValueError` and adds no hold.
- Add `Ship.get_capacity(hold) -> int | None`, which returns the hold's
  capacity (`None` for no limit). It raises `KeyError` for a hold that is
  not in use.
- Add `class HoldFull(CargoError)` to `ship.py`.
- A hold never holds more crates in total than its capacity. Every call
  that puts crates into a hold checks this before changing anything:
  `load`, and the receiving hold of `shift_all` and `seal_hold`. A call that
  would take the receiving hold over its capacity raises `HoldFull` and
  changes nothing: no crate moves, and `seal_hold` does not remove the hold.
  Filling a hold exactly to its capacity is allowed.
- A capacity never limits taking crates out: `unload`, and the hold that
  `shift_all` or `seal_hold` empties, are not checked.
- When a call has another problem as well (a hold not in use, a bad count,
  the same hold twice, not enough crates), which error it raises is
  unspecified.
- `undo` still restores the exact earlier state: an undone `seal_hold`
  brings the hold back with its capacity, and an undone `add_hold` removes
  the hold together with its capacity.

All existing behavior must keep working.
