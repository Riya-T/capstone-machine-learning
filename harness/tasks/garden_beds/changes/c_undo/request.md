Add an undo to `garden.py`, so a mistake in laying out the garden can be
taken back.

- Add `Garden.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among `add_bed`, `plant`, `pull`,
  `transplant_all` and `clear_bed`, and any other method of `Garden` that
  changes the beds or their plants (including methods added by other
  changes). Each further `undo` goes one call further back.
- Undoing a call puts every count, and the list of beds in its order, back
  to exactly what they were just before that call. A call that does several
  things is undone as a whole by a single `undo`:
  - an undone `transplant_all` puts every plant it moved back into the bed
    it came from;
  - an undone `clear_bed` brings the cleared bed back, with its plants and
    at its original position in `get_beds()`, and takes those plants out of
    the bed they were moved into; its name is in use again;
  - an undone `add_bed` removes the bed, and its name may then be added
    again.
- A `transplant_all` that moved 0 plants is still a call: `undo` reverses
  it like any other.
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `GardenError` and changes
  nothing.

All existing behavior must keep working.
