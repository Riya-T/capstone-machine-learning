Add an undo to `trails.py`, so a mistake made while editing the hut map
can be taken back.

- Add `TrailMap.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among the methods that change the
  state: `add_hut`, `add_trail`, `remove_trail`, `close_hut` and
  `merge_huts`, and any other method of `TrailMap` that changes the state.
  Each further `undo` goes one call further back.
- One `undo` reverses one whole call, even a call that changed several
  trails at once, such as `close_hut` or `merge_huts`.
- Undoing a call puts the list of huts in its order, and every hut's
  neighbors in their order, back exactly as they were just before that
  call:
  - an undone `remove_trail` puts the trail back at its old place in both
    huts' neighbors, not at the end;
  - an undone `close_hut` brings the hut back at its original position in
    `get_huts()`, with all its trails, each at its old place in the
    neighbors of both huts; its name is in use again;
  - an undone `merge_huts` brings the merged hut back the same way, and
    takes away the trails the merge gave to `into_hut`, so every hut's
    neighbors are as they were;
  - an undone `add_trail` removes that trail, and an undone `add_hut`
    removes the hut; the trail or the name may then be added again.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `TrailError` and changes
  nothing.

All existing behavior must keep working.
