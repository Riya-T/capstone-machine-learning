Several storekeepers now work on the same `parts.py` store from different
screens. Stop one of them from changing the store based on an outdated
view of it.

- Add `class VersionConflict(StoreError)` to `parts.py`.
- The store has a version number. It is 0 for a new `PartsStore` and goes
  up by 1 with every successful call that changes the store: `add_bin`,
  `stock`, `take`, `merge_bins`, `scrap_bin`, `set_frozen`, `undo`, and
  any other method that changes the store. Calls that raise leave it
  unchanged, and so do calls that only read (the `get_` methods).
- Add `PartsStore.get_version() -> int`.
- Every method that changes the store, including `undo`, takes a new
  keyword argument `expected_version=None`. When it is not `None` and is
  not equal to the store's current version, the call raises
  `VersionConflict` and changes nothing (the version stays the same too).
  When it is `None`, or equal to the current version, the call works as
  before. When a call has a wrong `expected_version` and also another
  problem, which error is raised is unspecified.
- `undo` is a change too: it takes back the most recent call as before,
  and the version goes up by 1. It does not go back to the number it had
  before the undone call.

All existing behavior must keep working.
