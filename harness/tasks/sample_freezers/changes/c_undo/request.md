Add undo to `freezers.py`, so that a mistaken call can be taken back.

- Add `Freezers.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet, among `add_freezer`, `store`,
  `discard`, `move`, `move_all` and `remove_freezer`. Each further `undo`
  goes one call further back. There is no redo.
- Undo puts back exactly what that call changed: which freezers are in use
  and their order in `get_freezers`, which freezer holds each sample, and
  the order of every freezer's samples in `get_samples`. In particular:
  - undoing `add_freezer` removes the freezer again, and its id may then be
    added again;
  - undoing `store` removes the sample, and its id may then be stored
    again;
  - undoing `discard` puts the sample back in its freezer, at the place it
    had in that freezer's order;
  - undoing `move` puts the sample back in the freezer it came from, at the
    place it had there;
  - undoing `move_all` puts the samples back in `from_freezer` in their old
    order and leaves `to_freezer` as it was before;
  - undoing `remove_freezer` brings the freezer back at its old place in
    `get_freezers`, with its samples in their old order, leaves
    `to_freezer` as it was before, and its id is in use again.
- A `move_all` or `remove_freezer` that moved 0 samples still counts as a
  call, and `undo` reverses it like any other.
- Calls that raised an error are not recorded, and neither are `find`, the
  `get_` methods and `undo` itself; `undo` skips over them.
- With nothing left to undo, `undo` raises `FreezerError` and changes
  nothing.

All existing behavior must keep working.
