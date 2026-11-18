Add an undo to `aquarium.py`, so a mistake made while rearranging the
tanks can be taken back.

- Add `Aquarium.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among the methods that change the
  state: `add_tank`, `add_fish`, `remove_fish`, `move_all` and
  `drain_tank`, and any other method of `Aquarium` that changes the state.
  Each further `undo` goes one call further back.
- One `undo` reverses one whole call, even a call that changed several
  tanks or species at once, such as `move_all` or `drain_tank`.
- Undoing a call puts every count, and the list of tanks in its order,
  back exactly as they were just before that call:
  - an undone `drain_tank` brings the drained tank back, with its fish and
    at its original position in `get_tanks()`, and takes those fish out of
    the tank they were moved to; its name is in use again;
  - an undone `add_tank` removes the tank, and its name may then be added
    again.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `AquariumError` and changes
  nothing.
- Whether a `move_all` that moved no fish counts as a call for `undo` is
  unspecified.

All existing behavior must keep working.
