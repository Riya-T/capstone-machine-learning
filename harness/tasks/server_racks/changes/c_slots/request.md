Give racks in `racks.py` an optional number of slots, the most servers they
can hold, since a real rack has room for only so many servers.

- `add_rack` takes a new keyword argument `slots=None`: the most servers
  the rack may hold. `None` means no limit. Anything else must be an `int`
  greater than 0; otherwise `add_rack` raises `ValueError` and adds no
  rack.
- Add `Racks.get_slots(rack) -> int | None`, which returns the rack's
  slots. It raises `KeyError` for a rack that is not in use.
- Add `class RackFull(RackError)` to `racks.py`.
- Every call that puts servers into a rack checks that rack's slots:
  `install`, `move` (`to_rack`), `migrate_all` (`to_rack`),
  `decommission_rack` (`into`), and every other method that puts servers
  into a rack, including methods added by other changes. When the
  receiving rack would then hold more servers than its slots, the call
  raises `RackFull` and changes nothing: no server moves, and
  `decommission_rack` does not remove the rack. Filling every slot is
  allowed.
- Only the receiving rack is checked: the rack the servers leave is not,
  and `remove` never raises `RackFull`.
- When a call would also raise another error, which error is raised is
  unspecified.
- `undo` still restores the exact earlier state: a rack brought back by
  undoing `decommission_rack` has its slots again.

All existing behavior must keep working.
