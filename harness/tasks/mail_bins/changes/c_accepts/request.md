Let each bin in `sorting.py` accept only parcels for certain destinations,
for example a bin that only takes parcels whose names start with `NY-`.

- Add `SortingRoom.set_accepts(bin_name, prefixes)` and
  `SortingRoom.get_accepts(bin_name) -> list[str] | None`. Both raise
  `KeyError` for a bin that is not in use.
- `prefixes` is either `None`, meaning the bin accepts every parcel, or a
  `list` of prefixes, each a non-empty `str`. Duplicates in the list are
  allowed and ignored, and an empty list means the bin accepts no parcel.
  Anything else, including a single `str`, raises `ValueError` and keeps
  the earlier setting. Each call replaces the bin's earlier setting.
- A bin with a list accepts a parcel when the parcel's name starts with
  one of the prefixes (case matters).
- Every new bin starts with `None`. That includes a bin added again under
  the name of a closed one: it does not keep the closed bin's setting.
- `get_accepts(bin_name)` returns `None`, or the prefixes without
  duplicates in alphabetical order.
- Add `class NotAccepted(SortingError)` to `sorting.py`.
- Every call that puts parcels into a bin checks that the bin accepts each
  of them: `drop`, and the receiving bin of `empty_bin_into` and
  `close_bin`. If even one parcel is not accepted, the call raises
  `NotAccepted` and changes nothing: no parcel moves, and `close_bin` does
  not close the bin. `empty_bin_into` or `close_bin` from an empty bin
  never raises `NotAccepted`.
- A setting does not affect parcels already in the bin: they stay, and can
  be picked, recalled or moved out as before. The setting of the bin the
  parcels leave is never checked. `set_accepts` moves no parcels.
- When a call also has another problem (a bin not in use, a parcel already
  in a bin, the same bin on both sides), which error it raises is
  unspecified.
- `undo` still puts back exactly the state from before the call it
  reverses, including every bin's setting: `set_accepts` is recorded and
  undone like the other calls that change the room, and an undone
  `close_bin` brings the bin back with its setting.

All existing behavior must keep working.
