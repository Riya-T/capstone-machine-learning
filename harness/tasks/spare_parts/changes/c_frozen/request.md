Let bins in `parts.py` be frozen while they are being counted, so nobody
changes them during a stocktake.

- Add `class BinFrozen(StoreError)` to `parts.py`.
- Add `PartsStore.set_frozen(bin_name, frozen)` and
  `PartsStore.get_frozen(bin_name) -> bool`. Both raise `KeyError` for a
  bin that is not in use. `frozen` is `True` (freeze the bin) or `False`
  (unfreeze it). Every new bin starts unfrozen.
- A frozen bin's counts can't change, and it can't be removed. These calls
  raise `BinFrozen` and change nothing:
  - `stock` and `take` on a frozen bin;
  - `merge_bins` when `source` or `into` (or both) is frozen;
  - `scrap_bin` of a frozen bin;
  - any other method that changes a bin's parts or removes a bin,
    including methods added later, when that bin is frozen.
- Frozen bins don't affect anything else: `add_bin`, the `get_` methods,
  and calls on other bins work as before.
- When a call would raise `BinFrozen` and also has another problem, which
  error is raised is unspecified.
- `undo` still puts back exactly the state from before the undone call:
  `set_frozen` is a call that `undo` reverses like any other. `set_frozen`
  changes no counts or bins.

All existing behavior must keep working.
