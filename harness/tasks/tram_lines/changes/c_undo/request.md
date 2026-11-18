Add an undo to `trams.py`, so a planning mistake can be taken back.

- Add `TramNetwork.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among the methods that change lines or
  stops: `add_line`, `add_stop`, `remove_stop`, `close_stop` and
  `merge_lines`, and any other method that changes lines or stops. Each
  further `undo` goes one call further back.
- Undoing a call puts every line's stops, in their order, and the list of
  lines, in its order, back to exactly what they were just before that call.
  One `undo` always takes back a whole call, however many lines it changed:
  - an undone `remove_stop` puts the stop back at its old position on the
    line;
  - an undone `close_stop` puts the stop back at its old position on every
    line it was taken off;
  - an undone `merge_lines` takes the stops it added off the first line, and
    brings the second line back with its stops, at its old position in
    `get_lines()`; its name is in use again;
  - an undone `add_line` removes the line, and its name may then be added
    again.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `TramError` and changes nothing.

All existing behavior must keep working.
