Some rooms in `rooms.py` need tidying up between meetings: the big hall
needs a while to set up, while the phone booths can be used back to back.
Make the number of free slots between two meetings of a room adjustable.
Today it is 0 everywhere.

- `RoomPlanner` takes a new keyword argument `gap=0`: the number of free
  slots needed between two bookings of the same room. A gap below 0 raises
  `ValueError`.
- `add_room` takes a new keyword argument `gap=None`. `None` means the room
  uses the planner's gap. Otherwise it sets the gap for that room alone; a
  gap below 0 raises `ValueError`, and no room is added.
- Add `RoomPlanner.get_gap(room) -> int`, which returns the gap that
  applies to the room. It raises `KeyError` for a room that does not exist.
- `book` and `get_free_rooms` use the room's own gap: two bookings of a
  room clash when they are `gap` or fewer slots apart. With a gap of 1, a
  booking in slot 5 keeps slots 4 and 6 of its room free, so the nearest
  other bookings can be in slots 3 and 7. With a gap of 2, they can be in
  slots 2 and 8. With the default gap of 0, only the same slot clashes, as
  before.

Gaps that are not `int`s are unspecified, and so is which error is raised
when `add_room` gets both an invalid gap and a room name that already
exists. All existing behavior must keep working.
