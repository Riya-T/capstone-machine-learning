Add an undo to `seating.py`, so a change to the seating chart can be taken
back when the host changes their mind.

- Add `SeatingChart.undo() -> None`. It reverses the most recent
  successful call that has not been undone yet among the methods that
  change the state: `add_table`, `seat`, `unseat`, `move_guest`,
  `merge_tables` and `clear_table`, and any other method of
  `SeatingChart` that changes the state. Each further `undo` goes one call
  further back.
- One `undo` reverses one whole call, even a call that moved or removed
  several guests at once, such as `merge_tables` or `clear_table`.
- Undoing a call puts every table's guests in their seating order, and the
  list of tables in its order, back exactly as they were just before that
  call:
  - an undone `unseat` or `move_guest` puts the guest back at their old
    place in their old table's seating order, not at the end;
  - an undone `clear_table` brings the table back, with its guests in
    their order and at its original position in `get_tables()`;
  - an undone `merge_tables` brings the merged table back, with its guests
    in their order and at its original position in `get_tables()`, and
    takes those guests off `into_table`;
  - an undone `add_table` removes the table, and its name may then be
    added again.
- Who is seated follows the undo: a guest whose `seat` was undone may be
  seated again, and a guest brought back by undoing `unseat` or
  `clear_table` is seated again, so seating them once more raises
  `SeatingError`.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `SeatingError` and changes
  nothing.

All existing behavior must keep working.
