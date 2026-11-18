Add an undo to `ship.py`, so a mistake in stowing the cargo can be taken
back.

- Add `Ship.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among `add_hold`, `load`, `unload`,
  `shift_all` and `seal_hold`, and any other method of `Ship` that changes
  the holds or their crates (including methods added by other changes).
  Each further `undo` goes one call further back.
- Undoing a call puts every count, and the list of holds in its order, back
  to exactly what they were just before that call. A call that does several
  things is undone as a whole by a single `undo`:
  - an undone `shift_all` puts every crate it moved back into the hold it
    came from;
  - an undone `seal_hold` brings the sealed hold back, with its crates and
    at its original position in `get_holds()`, and takes those crates out
    of the hold they were moved into; its name is in use again;
  - an undone `add_hold` removes the hold, and its name may then be added
    again.
- A `shift_all` that moved 0 crates is still a call: `undo` reverses it
  like any other.
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `CargoError` and changes
  nothing.

All existing behavior must keep working.
