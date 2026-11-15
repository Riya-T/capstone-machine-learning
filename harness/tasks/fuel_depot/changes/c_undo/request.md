Add undo to `depot.py`.

- Add `Depot.undo() -> None`. It reverses the most recent successful call
  of `add_tank`, `fill`, `drain`, `pump`, `pump_down` or `retire_tank` that
  has not been undone yet. Each further `undo` goes one call further back.
  There is no redo.
- Undoing a call puts back everything it changed: the levels, the logs, and
  the list of tanks with its order. An undone `retire_tank` brings the tank
  back into use, at its old place in `get_tanks()`, with its level and log
  as they were before the call. An undone `add_tank` removes the tank, and
  its id may then be added again.
- A `pump_down` or `retire_tank` that moved 0 litres still counts as a call
  and is undone like any other.
- Calls that raised are not recorded, and neither are the `get_...`
  methods.
- With nothing left to undo, `undo` raises `DepotError` and changes nothing.

All existing behavior must keep working.
