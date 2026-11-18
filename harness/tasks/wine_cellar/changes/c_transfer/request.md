Let several moves of bottles be made in `cellar.py` as one call that
succeeds or fails as a whole, for example when racks are rearranged for a
tasting and a half-done rearrangement would be worse than none.

- Add `Cellar.transfer(moves) -> int`. `moves` is a list of one or more
  moves, each a tuple `(from_rack, to_rack, vintage, count)` that moves
  `count` bottles of `vintage` from `from_rack` to `to_rack`. The moves are
  made in the order listed, and the call returns how many bottles it moved
  in total (the sum of the counts).
- Each move follows the usual rules: a rack that is not in use raises
  `KeyError`; a count of 0 or less, or the same rack on both sides, raises
  `ValueError`; moving more bottles of a vintage than the rack has at that
  point raises `NotEnoughBottles`.
- Each move sees the racks as the earlier moves of the same call left
  them: a move may pass on bottles that an earlier move in the list brought
  into a rack, and two moves may take from the same rack as long as the
  rack has enough bottles for both.
- The call succeeds or fails as a whole: if any move raises, `transfer`
  raises that error and none of the moves happen, not even the moves listed
  before the one that failed.
- When the moves have more than one problem, which error is raised is
  unspecified.

All existing behavior must keep working.
