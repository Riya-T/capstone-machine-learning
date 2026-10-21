Facilities wants to know how much the rooms in `rooms.py` are actually
used over a stretch of time, to decide which rooms to keep.

- Add `RoomPlanner.get_booked_minutes(room, start, end) -> int`: the number
  of minutes from `start` up to, but not including, `end` during which the
  room is booked. A booking that lies partly inside that window counts
  only for the minutes inside it. The gaps between bookings are not
  booked time. A room with no bookings in the window gives 0.
- Add `RoomPlanner.get_usage_ranking(start, end) -> list[tuple[str, int]]`:
  every room with its booked minutes in that window, as `(room, minutes)`,
  most minutes first. Rooms with the same number of minutes, including 0,
  stay in the order they were added.
- The window's `start` and `end` are checked like the times in `book`, and
  raise `ValueError` the same way. For `get_booked_minutes`, `KeyError` for
  a room that does not exist comes before `ValueError`.

All existing behavior must keep working.
