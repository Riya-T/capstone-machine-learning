Facilities wants to know how much the rooms in `rooms.py` are actually
used over a stretch of the day, to decide which rooms to keep.

- Add `RoomPlanner.get_booked_slots(room, first, last) -> int`: how many
  of the room's bookings are in slots `first` up to, but not including,
  `last`. A room with no bookings there gives 0. For example, with
  bookings of `"oak"` in slots 10, 11 and 20, `get_booked_slots("oak", 10,
  12)` is 2, `get_booked_slots("oak", 11, 20)` is 1 and
  `get_booked_slots("oak", 0, 100)` is 3.
- Add `RoomPlanner.get_usage_ranking(first, last) -> list[tuple[str, int]]`:
  every room with its booked slots in that stretch, as `(room, slots)`,
  most slots first. Rooms with the same number, including 0, stay in the
  order they were added.
- A `first` below 0, or a `last` that is not greater than `first`, raises
  `ValueError` in both methods. Values that are not `int`s are
  unspecified. `get_booked_slots` raises `KeyError` for a room that does
  not exist; which error it raises when the room does not exist and the
  stretch is invalid is unspecified.

All existing behavior must keep working.
