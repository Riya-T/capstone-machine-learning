Several operators edit the same racks from different consoles. Let
`racks.py` detect when a change is based on a state that someone else has
changed in the meantime.

- Add `class VersionConflict(RackError)` to `racks.py`.
- Add `Racks.get_version() -> int`. It is 0 for a new `Racks` object and
  goes up by exactly 1 with every successful call that changes the racks:
  `add_rack`, `install`, `remove`, `move`, `migrate_all`,
  `decommission_rack`, `undo`, and every other method that changes the
  racks. It goes up by 1 per call, however many servers the call moves;
  a `migrate_all` or `decommission_rack` that moved 0 servers counts too.
  Calls that raise, and the `get_` methods, leave it unchanged.
- Every method that changes the racks, including `undo`, takes a new
  keyword argument `expected_version=None`. When it is not `None` and is
  not equal to `get_version()`, the call raises `VersionConflict` and
  changes nothing. When it is equal, or `None`, the call works as before.
- `undo` never puts an older version number back: like every other change,
  it raises the version by 1, while it still restores the exact earlier
  racks and servers.
- When a call has a version conflict and another problem, which error is
  raised is unspecified.

All existing behavior must keep working.
