Stop two lock keepers from overwriting each other's changes to the network
in `canals.py`: a change based on an old view of the network must be
refused.

- Add `class VersionConflict(CanalError)` to `canals.py`.
- The network has a version number. It is 0 for a new network and goes up
  by 1 with every successful call that changes the network: `add_lock`,
  `connect`, `disconnect`, `close_lock`, `merge_locks`, `set_max_channels`,
  `undo`, and any other method that changes the network. Calls that raise,
  and calls that only read (the `get_` methods), leave it unchanged.
- Add `CanalNetwork.get_version() -> int`.
- Every method that changes the network takes a new keyword argument
  `expected_version=None`. When it is not `None` and is not equal to the
  current version, the call raises `VersionConflict` and changes nothing,
  so the version stays the same as well. With `None`, or with the current
  version, the call works as before. When a call has another problem as
  well, which error is raised is unspecified.
- `undo` still puts the locks, channels and limits back exactly as they
  were before the call it reverses, but not the version: `undo` is itself
  a change, so the version goes up by 1 and never goes back.

All existing behavior must keep working.
