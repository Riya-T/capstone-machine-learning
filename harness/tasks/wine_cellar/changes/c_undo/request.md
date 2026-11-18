Add an undo to `cellar.py`, so a mistake in moving bottles around can be
taken back.

- Add `Cellar.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among the calls that change the cellar:
  `add_rack`, `store`, `take`, `relocate_all` and `decommission_rack`, and
  any method added later that changes the cellar. Each further `undo` goes
  one call further back.
- Undoing a call puts every count, and the list of racks in its order, back
  to what they were just before that call:
  - an undone `relocate_all` takes the moved bottles back out of the
    receiving rack and returns them to the rack they came from; the bottles
    the receiving rack had before stay where they are;
  - an undone `decommission_rack` brings the rack back, with its bottles and
    at its original position in `get_racks()`, and takes those bottles out
    of the rack they were moved into; its name is in use again;
  - an undone `add_rack` removes the rack, and its name may then be added
    again.
- A call that changes two racks at once (`relocate_all`,
  `decommission_rack`) is one call: a single `undo` reverses all of it.
- A `relocate_all` or `decommission_rack` that moved 0 bottles is still a
  call: `undo` reverses it like any other (an undone `decommission_rack` of
  an empty rack brings the rack back).
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `CellarError` and changes
  nothing.

All existing behavior must keep working.
