Add an undo to `drying.py`, so a mistake in moving the bundles can be taken
back.

- Add `DryingRoom.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among `add_rack`, `hang`, `take_down`,
  `shift_all` and `dismantle_rack`, and any method added later that changes
  the room. Each further `undo` goes one call further back.
- Undoing a call puts every count, and the list of racks in its order, back
  to what they were just before that call. A call that changed several
  racks or herbs is undone as a whole by one `undo`:
  - an undone `shift_all` puts every bundle it moved back on `from_rack`
    and takes it off `to_rack`;
  - an undone `dismantle_rack` brings the rack back, with its bundles and
    at its original position in `get_racks()`, and takes those bundles off
    the rack they were moved to; its name is in use again;
  - an undone `take_down` of a herb's last bundles lists the herb again;
  - an undone `add_rack` removes the rack, and its name may then be added
    again.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `DryingError` and changes
  nothing.

All existing behavior must keep working.
