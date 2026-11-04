Assistants now move meetings in `rooms.py` to other slots, and two
assistants moving the same meeting at once can undo each other's move
without noticing. Add moving, and give every booking a version number so a
caller can say which state of the booking they are changing.

- Add `RoomPlanner.reschedule(booking_id, slot, expected_version=None)`,
  which moves the booking to another slot of the same room. The new slot is
  checked like in `book`, with the room's own gap: it raises `ValueError`
  for a slot below 0, and `RoomBusy` when the booking would clash with
  another booking of the room. The booking's own old slot never counts: a
  booking can stay in its slot, and in a room with a gap of 1, a booking in
  slot 5 can move to slot 6.
- Each booking has a version. It is 1 when the booking is made and goes up
  by 1 with every successful `reschedule` of that booking, even one to the
  same slot. A failed call never changes it, and changing one booking never
  changes another booking's version.
- Add `RoomPlanner.get_version(booking_id) -> int`. It raises `KeyError`
  for a booking that does not exist.
- When `expected_version` is `None`, no version check is made. Otherwise,
  if it is not equal to the booking's current version, `reschedule` raises
  `VersionConflict` and changes nothing.
- Add `class VersionConflict(BookingError)` to `rooms.py`. It is not a
  `RoomBusy`.

`reschedule` raises:

- `KeyError` for a booking that does not exist;
- `ValueError` for a slot below 0;
- `VersionConflict`;
- `RoomBusy`.

Which of these is raised when one call has several problems is
unspecified, and so are slots that are not `int`s.

All existing behavior must keep working.
