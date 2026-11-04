Two assistants rescheduling the same meeting in `rooms.py` at once can
undo each other's move without noticing. Give every booking a version
number so a caller can say which state of the booking they are changing.

- Each booking has a version. It is 1 when the booking is made and goes up
  by 1 with every successful `reschedule` of that booking, even one to the
  same times. A failed call never changes it, and changing one booking
  never changes another booking's version.
- Add `RoomPlanner.get_version(booking_id) -> int`. It raises `KeyError`
  for a booking that does not exist.
- `reschedule` takes a new keyword argument `expected_version=None`. When
  it is `None`, rescheduling works as before. Otherwise, if it is not equal
  to the booking's current version, `reschedule` raises `VersionConflict`
  and changes nothing.
- Add `class VersionConflict(BookingError)` to `rooms.py`. It is not a
  `RoomBusy`.

`reschedule` raises:

- `KeyError` for a booking that does not exist;
- `ValueError` for invalid times;
- `VersionConflict`;
- `RoomBusy`.

Which of these is raised when one call has several problems is
unspecified.

All existing behavior must keep working.
