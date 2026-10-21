Add an undo to `lights.py` that takes back commands, newest first.

- Add `class NothingToUndo(Exception)` to `lights.py`.
- Add `LightGrid.undo() -> None`. It takes back the most recent `turn_on`,
  `turn_off` or `toggle` that has not been taken back yet: every light in
  that command's rectangle gets back exactly the brightness it had just
  before the command. Calling `undo` again takes back the command before
  that one, and so on.
- Only commands that succeeded can be taken back; a call that raised is not
  a command. A command that changed no light (for example `turn_off` on
  lights that are already off) still counts, and taking it back changes
  nothing.
- `lock` and `unlock` are not commands: `undo` never takes them back and
  skips over them. Taking a command back restores its lights even if they
  have been locked since.
- Add `LightGrid.get_undo_count() -> int`: how many commands can still be
  taken back.
- With nothing left to take back, `undo` raises `NothingToUndo` and
  changes nothing.
- There is no redo: commands given after an `undo` are recorded as usual.

All existing behavior must keep working.
