Add an undo to `sorting.py`, so a mistake in sorting parcels can be taken
back.

- Add `SortingRoom.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among the calls that change the room:
  `add_bin`, `drop`, `pick`, `recall`, `empty_bin_into` and `close_bin`,
  and any method added later that changes the room. Each further `undo`
  goes one call further back.
- Undoing a call puts the list of bins, in its order, and the parcels of
  every bin, in their order, back exactly as they were just before that
  call:
  - an undone `pick` puts the parcel back at the front of its bin, and an
    undone `recall` puts the parcel back at its original position in its
    bin; either way the parcel is in that bin again, so it cannot be
    dropped anywhere until it leaves again;
  - an undone `empty_bin_into` takes the moved parcels off the back of the
    receiving bin and puts them back into the bin they came from, in their
    order; the parcels the receiving bin had before stay where they are;
  - an undone `close_bin` brings the bin back, with its parcels in their
    order and at its original position in `get_bins()`, and takes those
    parcels out of the bin they were moved into; its name is in use again;
  - an undone `drop` removes the parcel, which may then be dropped again;
    an undone `add_bin` removes the bin, and its name may then be added
    again.
- A call that changes two bins at once (`empty_bin_into`, `close_bin`) is
  one call: a single `undo` reverses all of it. An `empty_bin_into` or
  `close_bin` that moved 0 parcels is still a call: `undo` reverses it like
  any other (an undone `close_bin` of an empty bin brings the bin back).
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `SortingError` and changes
  nothing.

All existing behavior must keep working.
