Let tables in `seating.py` be locked once their place cards are printed,
so nobody joins or leaves them by mistake.

- Add `SeatingChart.lock_table(table)` and `SeatingChart.unlock_table(table)`,
  and `SeatingChart.get_locked_tables() -> list[str]`, which returns the
  locked tables in the order of `get_tables()`. `lock_table` and
  `unlock_table` raise `KeyError` for a table that is not in use. New
  tables are not locked. Locking a locked table, or unlocking a table that
  is not locked, is unspecified.
- Add `class TableLocked(SeatingError)` to `seating.py`.
- No guest may join or leave a locked table. These calls raise
  `TableLocked` and change nothing when they involve a locked table:
  - `seat` at a locked table;
  - `unseat` of a guest at a locked table;
  - `move_guest` of a guest at a locked table, or to a locked table;
  - `merge_tables` when either of the two tables is locked;
  - `clear_table` of a locked table.
- `get_guests`, `get_tables` and `add_table` work as before, and so does
  everything at the tables that are not locked.
- `unlock_table` lifts the lock: the table works as before.
- `lock_table` and `unlock_table` are recorded like the other calls that
  change the state: `undo` of a `lock_table` unlocks the table again, and
  `undo` of an `unlock_table` locks it again. `undo` still puts back the
  exact earlier state, locks included, and a lock never stops `undo`.
- When a call has more than one problem, which error is raised is
  unspecified.

All existing behavior must keep working.
