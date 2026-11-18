Let bins in `crib.py` be locked, for example while a bin is being counted.
No tool may go into or come out of a locked bin.

- Add `ToolCrib.lock_bin(name) -> None` and `ToolCrib.unlock_bin(name) ->
  None`. Both raise `KeyError` for a bin that is not in use. New bins are
  unlocked, including a bin added again under the name of a closed one.
  Locking a locked bin, or unlocking a bin that is not locked, raises
  `CribError` and changes nothing.
- Add `class BinLocked(CribError)` to `crib.py`.
- These calls raise `BinLocked` and change nothing when a bin they would
  put a tool into or take a tool out of is locked:
  - `add_tool` into a locked bin;
  - `check_out` of a tool that is in a locked bin;
  - `return_tool` into a locked bin (the person keeps the tool);
  - `return_all` into a locked bin (no tool is returned);
  - `close_bin` when either of the two bins is locked, even when the bin
    to close is empty.
- When a call has another problem as well, which error is raised is
  unspecified.
- `get_tools` and `get_holder` work as before on locked bins and their
  tools. Other bins are not affected.
- `unlock_bin` lifts the lock: the bin works as before.
- `lock_bin` and `unlock_bin` change the crib, so `undo` reverses them like
  every other such call: an undone `lock_bin` unlocks the bin again, and an
  undone `unlock_bin` locks it again. `undo` still puts everything back
  exactly as it was before the call it reverses.

All existing behavior must keep working.
