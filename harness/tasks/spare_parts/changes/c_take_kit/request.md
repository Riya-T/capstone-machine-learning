Let `parts.py` hand out a whole repair kit from one bin in one call, so a
kit is either complete or not handed out at all.

- Add `PartsStore.take_kit(bin_name, kit) -> int`. `kit` is a `dict` that
  maps part numbers to counts, for example `{"bolt": 4, "nut": 4}`. The
  call takes `count` parts of each part number in `kit` out of the bin,
  exactly as if `take(bin_name, part, count)` were called for each of
  them, and returns how many parts it took in total.
- It raises `KeyError` for a bin that is not in use, `ValueError` when any
  count in `kit` is not greater than 0, and `NotEnoughParts` when the bin
  has fewer parts of any part number than the kit asks for.
- The kit is handed out completely or not at all: if the call raises,
  nothing is taken, including the part numbers of the kit that the bin
  does have enough of.
- What an empty `kit` does is unspecified.

All existing behavior must keep working.
