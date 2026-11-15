Add an undo to `farm.py`, so a mistake in moving the herd can be taken
back.

- Add `Farm.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among `add_paddock`, `arrive`, `depart`,
  `move`, `move_all` and `close_paddock`. Each further `undo` goes one call
  further back.
- Undoing a call puts every count, and the list of paddocks in its order,
  back to what they were just before that call:
  - an undone `close_paddock` brings the closed paddock back, with its
    animals and at its original position in `get_paddocks()`, and takes
    those animals out of the paddock they were moved to; its name is in
    use again;
  - an undone `add_paddock` removes the paddock, and its name may then be
    added again.
- A `move_all` or `close_paddock` that moved 0 animals is still a call:
  `undo` reverses it like any other (an undone `close_paddock` of an empty
  paddock brings the paddock back).
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `FarmError` and changes nothing.

All existing behavior must keep working.
