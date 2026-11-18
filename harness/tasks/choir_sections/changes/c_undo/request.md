Add an undo to `choir.py`, so a mistake in arranging the choir can be taken
back.

- Add `Choir.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among the calls that change the choir:
  `add_section`, `add_singer`, `remove_singer`, `move_singer`, `move_all`
  and `merge_sections`, and every other method of `Choir` that changes the
  choir, whether it exists now or is added later. Each further `undo` goes
  one call further back.
- Undoing a call puts the choir back exactly as it was just before that
  call: the list of sections in its order, and the singers of each section
  in their order. One `undo` takes back the whole call, even when the call
  moved several singers:
  - an undone `remove_singer` brings the singer back at their old place in
    their section, not at the end; their name is taken again;
  - an undone `move_singer` takes the singer out of the section they were
    moved to and puts them back at their old place in their old section;
  - an undone `move_all` takes the moved singers out of `into` and puts
    them back into `source` in their order;
  - an undone `merge_sections` brings the source section back at its
    original position in `get_sections()`, with its singers in their
    order, and takes those singers out of the section they were merged
    into; the source section's name is in use again;
  - an undone `add_section` or `add_singer` removes the section or the
    singer again, and the name may then be added again.
- A `move_all` or `merge_sections` of an empty section is still a call:
  `undo` reverses it like any other (an undone `merge_sections` of an empty
  section brings the empty section back).
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `ChoirError` and changes
  nothing.

All existing behavior must keep working.
