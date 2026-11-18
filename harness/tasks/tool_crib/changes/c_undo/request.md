Add an undo to `crib.py`, so a mistaken call can be taken back.

- Add `ToolCrib.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among `add_bin`, `add_tool`, `check_out`,
  `return_tool`, `return_all` and `close_bin`, and any method added later
  that changes the crib. Each further `undo` goes one call further back.
- Undoing a call puts everything back exactly as it was just before that
  call: which bins are in use, the tools in each bin in their order, who
  has each checked-out tool, and the order in which each person checked
  their tools out (so a later `return_all` returns them in that order). A
  call that changed several things is undone as a whole by one `undo`:
  - an undone `check_out` puts the tool back at its old position in its
    bin, not at the end;
  - an undone `return_tool` takes the tool out of the bin and gives it back
    to the person; an undone `return_all` does this for every tool it
    returned;
  - an undone `close_bin` brings the bin back with its tools in their
    order and takes those tools off the end of the other bin; its name is
    in use again;
  - an undone `add_bin` removes the bin, and an undone `add_tool` removes
    the tool; their names may then be added again.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `CribError` and changes nothing.

All existing behavior must keep working.
