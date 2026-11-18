Let each bed in `garden.py` limit which species may grow in it, for example
a shady bed that only takes ferns and mint.

- `add_bed(name, allowed=None)` takes an optional list of the species
  allowed in the bed. `None` (the default) means any species may grow
  there. The list may contain duplicates, which are ignored, and an empty
  list means no species may be planted there.
- Add `Garden.get_allowed(bed) -> list[str] | None`, which returns `None`,
  or the bed's allowed species without duplicates in alphabetical order. It
  raises `KeyError` for a bed that is not in use.
- Add `class NotAllowed(GardenError)` to `garden.py`.
- Every call that puts plants into a bed checks that their species is
  allowed there: `plant`, and the receiving bed of `transplant_all` and
  `clear_bed`. If a species is not allowed, the call raises `NotAllowed` and
  changes nothing.
- `transplant_all` and `clear_bed` check every species they would move
  before moving any plant: if even one of them is not allowed, nothing
  moves and `clear_bed` does not remove the bed. Only species that have
  plants in the bed being emptied are checked.
- The allowed species never limit taking plants out: `pull`, and the bed
  that `transplant_all` or `clear_bed` empties, are not checked.
- When a call has another problem as well (a bed not in use, a bad count,
  the same bed twice, not enough plants), which error it raises is
  unspecified.
- `undo` still restores the exact earlier state: an undone `clear_bed`
  brings the bed back with its allowed species, and an undone `add_bed`
  removes the bed together with them.

All existing behavior must keep working.
