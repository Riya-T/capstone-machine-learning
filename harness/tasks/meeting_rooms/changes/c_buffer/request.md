The 10-minute gap between meetings in `rooms.py` does not suit every
building: the big hall needs longer to set up, and the phone booths need
no gap at all. Make the gap adjustable.

- `RoomPlanner` takes a new keyword argument `gap=10`: the number of
  minutes needed between two bookings of the same room. It must be an
  `int` of 0 or more (not a `bool`); anything else raises `ValueError`.
- `add_room` takes a new keyword argument `gap=None`. `None` means the room
  uses the planner's gap. Otherwise it must be an `int` of 0 or more (not a
  `bool`) and sets the gap for that room alone; anything else raises
  `ValueError` and no room is added. An invalid gap counts as an invalid
  argument, so it is reported before `BookingError` for a room name that
  already exists.
- Add `RoomPlanner.get_gap(room) -> int`, which returns the gap that
  applies to the room. It raises `KeyError` for a room that does not exist.
- Every rule that used the fixed 10 minutes now uses the room's own gap:
  `book`, `reschedule` and `get_free_rooms` all apply it. With a gap of 0,
  a booking may start at the very minute the previous one ends, but
  bookings still may not overlap.

All existing behavior must keep working.
