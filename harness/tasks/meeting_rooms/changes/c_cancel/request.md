Meetings in `rooms.py` sometimes get called off. Let a booking be
cancelled so its slot is free again, while keeping a record of what was
cancelled.

- Add `RoomPlanner.cancel(booking_id, expected_version=None)`. It removes
  the booking from its room. `expected_version` works as in `reschedule`:
  when it is given and is not the booking's current version, `cancel`
  raises `VersionConflict` and changes nothing.
- A cancelled booking no longer exists: `get_booking`, `get_version`,
  `reschedule` and `cancel` raise `KeyError` for it, and it is not in
  `get_bookings`. Its slot is free again for `book`, `reschedule` and
  `get_free_rooms`. In a room with a gap, so are the free slots that the
  gap kept around it, unless another booking of the room still needs them.
- A booking id stays used after its booking is cancelled: `book` with that
  id raises `BookingError`, in any room.
- Add `RoomPlanner.get_cancelled(room) -> list[str]`: the ids of the
  room's cancelled bookings, in the order they were cancelled. It raises
  `KeyError` for a room that does not exist. A room with no cancelled
  bookings gives `[]`.

`cancel` raises `KeyError` for a booking that does not exist (or was
already cancelled). Which error is raised when such a call also has an
`expected_version` is unspecified.

All existing behavior must keep working.
