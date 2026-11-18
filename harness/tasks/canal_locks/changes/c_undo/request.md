Add an undo to `canals.py`, so a mistake in rebuilding the canal network
can be taken back.

- Add `CanalNetwork.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among `add_lock`, `connect`,
  `disconnect`, `close_lock` and `merge_locks`, and any other method that
  changes the network (including methods added later). Each further `undo`
  goes one call further back.
- Undoing a call puts the list of locks, and every lock's channels in
  their order, back exactly as they were just before that call:
  - an undone `disconnect` puts the channel back at its old position in
    the channels of both locks;
  - an undone `close_lock` brings the lock back at its old position in
    `get_locks()`, with all its channels, each at its old position in the
    channels of both locks; its name is in use again;
  - an undone `merge_locks` removes the channels it added to `into`, and
    brings `source` back at its old position with all its channels, each
    at its old position in the channels of both locks;
  - an undone `add_lock` removes the lock, and an undone `connect` removes
    the channel.
- A call that changes several things at once is one call: one `undo`
  reverses all of it. A `close_lock` that removed 0 channels, or a
  `merge_locks` that added 0, is still a call that `undo` reverses.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `CanalError` and changes
  nothing.

All existing behavior must keep working.
