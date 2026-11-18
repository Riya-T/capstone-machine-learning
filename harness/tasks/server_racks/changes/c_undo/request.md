Add an undo to `racks.py`, so that a mistake, such as migrating a rack into
the wrong one, can be taken back.

- Add `Racks.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among the calls that change the racks:
  `add_rack`, `install`, `remove`, `move`, `migrate_all`,
  `decommission_rack`, and every other method that changes the racks or
  their servers, including methods added by other changes. Each further
  `undo` goes one call further back.
- Undoing a call puts every rack, with its servers in their order, and the
  list of racks in its order, back to exactly what they were just before
  that call. A call that moved several servers is undone as a whole by one
  `undo`:
  - an undone `remove` puts the server back at its old position in its
    rack, and its name is installed again;
  - an undone `move` puts the server back at its old position in the rack
    it came from;
  - an undone `migrate_all` puts every server it moved back into
    `from_rack`, in their old order, and takes them out of `to_rack`;
  - an undone `decommission_rack` brings the rack back, with its servers
    in their order and at its original position in `get_racks()`, and
    takes those servers out of `into`; its name is in use again;
  - an undone `install` takes the server out again, and its name may then
    be installed again;
  - an undone `add_rack` removes the rack, and its name may then be added
    again.
- A `migrate_all` or `decommission_rack` that moved 0 servers is still a
  call: `undo` reverses it like any other (an undone `decommission_rack` of
  an empty rack brings the rack back).
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `RackError` and changes nothing.

All existing behavior must keep working.
