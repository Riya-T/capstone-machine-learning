Add homerooms to `roster.py`: named rooms that group students of one grade.

- Add `Roster.assign_homeroom(name, room)`, which puts the student in
  `room`. A student is in at most one homeroom, so assigning a student who
  already has one moves them to the new room, where they join at the end.
  Assigning a student to the room they are already in changes nothing. New
  students have no homeroom.
- A homeroom belongs to one grade: assigning a student to a room that
  currently holds a student of another grade raises `RosterError`.
- Add `Roster.get_homeroom(name) -> str | None`: the student's homeroom, or
  `None` when they have none.
- Add `Roster.get_homeroom_students(room) -> list[str]`: the names in that
  room, in the order they joined it; `[]` for a room nobody is in.
- Add `Roster.get_homerooms() -> list[str]`: the rooms that currently have
  at least one student, in the order each room was first used. A room that
  empties and is used again keeps its original place.
- A student who changes grade through `move_students` leaves their homeroom
  (`get_homeroom` then returns `None`); a student moved to the grade they
  are already in keeps it. A move that raises changes no homerooms.

`assign_homeroom` and `get_homeroom` raise `KeyError` for a name that is not
on the roster, and `assign_homeroom` and `get_homeroom_students` raise
`ValueError` when the room is an empty string or `None`. In each case
nothing changes. When one call has several problems (an unknown name, an
invalid room, a grade mismatch), which error it raises is unspecified. All
existing behavior must keep working.
