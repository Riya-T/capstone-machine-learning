Let each rack in `drying.py` have a limit on how many bundles it holds,
since a rack only bears so much weight.

- Add `DryingRoom.set_capacity(rack, capacity) -> None` and
  `DryingRoom.get_capacity(rack) -> int | None`. Both raise `KeyError` for a
  rack that is not in use.
- `capacity` is either `None`, meaning no limit, or an `int` greater than
  0. Anything else (such as 0 or a negative number) raises `ValueError` and
  changes nothing. Each call replaces the rack's earlier capacity.
- Every new rack has capacity `None`, including a rack added again under
  the name of a dismantled one: it does not keep the old rack's capacity.
- Add `class RackFull(DryingError)` to `drying.py`.
- A capacity limits the total number of bundles on the rack, of all herbs
  together. Every call that puts bundles on a rack checks the receiving
  rack: `hang`, the `to_rack` of `shift_all`, and the `into` rack of
  `dismantle_rack`. If that rack would then hold more bundles than its
  capacity, the call raises `RackFull` and changes nothing: `shift_all` and
  `dismantle_rack` move no bundle, and `dismantle_rack` does not remove the
  rack. Filling a rack exactly to its capacity is allowed.
- A capacity below the number of bundles a rack already holds is allowed:
  the bundles stay and can be taken down or moved away as before, and every
  call that would put more bundles on the rack raises `RackFull`.
- `take_down` never checks a capacity, and the capacity of the rack the
  bundles leave is never checked.
- When a call has another problem as well, which error is raised is
  unspecified.
- Every successful `set_capacity` changes the room, so `undo` reverses it
  like every other such call: an undone `set_capacity` gives the rack back
  the capacity it had before. `undo` still puts everything back exactly as
  it was before the call it reverses; an undone `dismantle_rack` brings the
  rack back with its capacity too.

All existing behavior must keep working.
