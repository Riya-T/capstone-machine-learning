Let each rack in `cellar.py` have a capacity, the most bottles it can hold
in total, for example a small rack with room for 12 bottles.

- Add `Cellar.set_capacity(rack, capacity)` and
  `Cellar.get_capacity(rack) -> int | None`. Both raise `KeyError` for a
  rack that is not in use.
- `capacity` is either `None`, meaning no limit, or an `int` greater than 0
  that is at least the number of bottles (of all vintages) in the rack now.
  Anything else raises `ValueError` and keeps the earlier setting. Each
  call replaces the rack's earlier setting.
- Every new rack starts with `None`. That includes a rack added again under
  the name of a decommissioned one: it does not keep the old rack's
  capacity.
- Add `class RackFull(CellarError)` to `cellar.py`.
- Every call that puts bottles into a rack checks that the rack's total
  number of bottles, of all vintages, stays at or below its capacity:
  `store`, and the receiving rack of `relocate_all` and
  `decommission_rack`. If the total would go above the capacity, the call
  raises `RackFull` and changes nothing; in particular `decommission_rack`
  then does not decommission the rack.
- `relocate_all` and `decommission_rack` from an empty rack never raise
  `RackFull`.
- `take` never checks the capacity, and the capacity of the rack the
  bottles leave is never checked. `set_capacity` changes no counts.
- When a call also has another problem (a rack not in use, a bad count,
  the same rack on both sides, not enough bottles), which error it raises
  is unspecified.
- `undo` still puts back exactly the state from before the call it
  reverses, including every rack's capacity: `set_capacity` is recorded and
  undone like the other calls that change the cellar, and an undone
  `decommission_rack` brings the rack back with its capacity.

All existing behavior must keep working.
