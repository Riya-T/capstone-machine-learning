Add two ways to look parcels up in `sorting.py`, for example to tell a
customer where their parcel is waiting.

- Add `SortingRoom.get_bin_of(parcel) -> str | None`. It returns the name
  of the bin that holds the parcel, or `None` when no bin holds it (it was
  never dropped, or it was picked or recalled).
- Add `SortingRoom.find_parcels(prefix, bin_name=None) -> list[str]`. It
  returns the parcels whose names start with `prefix`, a non-empty `str`
  (case matters).
  - Without `bin_name` it looks in every bin: the parcels are listed bin by
    bin in the order of `get_bins()`, and within a bin from front to back.
  - With `bin_name` it looks only in that bin, front to back, and raises
    `KeyError` if that bin is not in use.
  - With no matching parcel it returns an empty list.
- Both methods only look: they change nothing.

All existing behavior must keep working.
