Add an undo to `parts.py`, so a storekeeper's mistake can be taken back.

- Add `PartsStore.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among `add_bin`, `stock`, `take`,
  `merge_bins`, `scrap_bin`, and any other method that changes the bins or
  their parts, including methods added later. Each further `undo` goes one
  call further back.
- Undoing a call puts every count, and the list of bins in its order, back
  to exactly what they were just before that call. A call that changed
  several things is undone as a whole:
  - an undone `merge_bins` brings bin `source` back, with all its parts and
    at its old position in `get_bins()`, and takes those parts out of bin
    `into` again; its name is in use again;
  - an undone `scrap_bin` brings the bin back with all its parts, at its
    old position in `get_bins()`; its name is in use again;
  - an undone `take` of a bin's last parts of a part number lists that part
    number in `get_parts` again;
  - an undone `add_bin` removes the bin, and its name may then be added
    again.
- A `merge_bins` or `scrap_bin` of an empty bin is still a call: `undo`
  reverses it like any other (the empty bin comes back).
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `StoreError` and changes
  nothing.

All existing behavior must keep working.
