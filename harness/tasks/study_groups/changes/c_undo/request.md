Add an undo to `groups.py`, so a mistake in arranging the groups can be
taken back.

- Add `StudyGroups.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among `add_group`, `join`, `leave`,
  `swap_students` and `dissolve_group`, and any other method of
  `StudyGroups` that changes the groups (including methods added by other
  changes). Each further `undo` goes one call further back.
- Undoing a call puts every group's members, in their order, and the list
  of groups in its order, back to exactly what they were just before that
  call. A call that does several things is undone as a whole by a single
  `undo`:
  - an undone `swap_students` puts both students back at their old
    positions;
  - an undone `dissolve_group` brings the dissolved group back, with its
    members in their order and at its original position in `get_groups()`,
    and takes those students out of the group they were moved into; its
    name is in use again;
  - an undone `leave` puts the student back in their group at their old
    position;
  - an undone `join` takes the student out again, so they may join a group
    later;
  - an undone `add_group` removes the group, and its name may then be added
    again.
- A `dissolve_group` that moved 0 students is still a call: `undo` reverses
  it like any other (the empty group comes back).
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `GroupError` and changes
  nothing.

All existing behavior must keep working.
