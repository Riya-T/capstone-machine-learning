Let each lock in `canals.py` limit how many channels it can have, because
the basin of a small lock only has room for so many gates.

- Add `CanalNetwork.set_max_channels(name, limit)` and
  `CanalNetwork.get_max_channels(name) -> int | None`. Both raise
  `KeyError` for a lock that is not in use.
- `limit` is either `None`, meaning no limit, or an `int` of 1 or more.
  Anything else raises `ValueError`, and so does a limit smaller than the
  number of channels the lock has now. In each case nothing changes. Each
  call replaces the lock's earlier limit.
- Every new lock starts with `None`. That includes a lock added again
  under the name of a closed or merged one: it does not keep the old
  lock's limit.
- Add `class TooManyChannels(CanalError)` to `canals.py`.
- `connect` raises `TooManyChannels` and changes nothing when either lock
  already has as many channels as its limit allows.
- `merge_locks` raises `TooManyChannels` and changes nothing (`source` is
  not removed) when `into` would end up with more channels than its limit
  allows, counted after the whole merge. No other lock gains channels in a
  merge, so only the limit of `into` is checked.
- Any other method that adds channels obeys the limits in the same way.
  `disconnect` and `close_lock` never raise `TooManyChannels`.
- When a call has another problem as well (a lock that is not in use, the
  same lock twice, locks that are already joined), which error is raised
  is unspecified.
- `undo` still restores the exact earlier state, now including every
  lock's limit: `set_max_channels` is a recorded call like the others, so
  `undo` reverses it, and undoing any call puts every limit back as it was
  just before that call. `undo` itself is never blocked by a limit.

All existing behavior must keep working.
