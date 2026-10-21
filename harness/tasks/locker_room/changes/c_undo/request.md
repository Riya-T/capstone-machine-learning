Let the desk take back mistakes in `lockers.py`: an item handed in or
handed back by accident can be undone, most recent first.

- Add `LockerRoom.undo() -> str`. It reverses the most recent successful
  `store` or `retrieve` that has not been undone yet, and returns the id of
  that call's item. Calling it again reverses the one before, and so on,
  back to the first. Other calls (`add_locker`, `set_out_of_order`,
  `set_in_service`, reads, and calls that raised) are not reversed and are
  skipped over.
- Undoing a `store`: the item is no longer in a locker, the locker is empty
  again, and the fee that this `store` took is taken off the takings.
- Undoing a `retrieve`: the item is back in the locker it was taken from,
  and no fee is taken. If that locker is out of order now, `undo` raises
  `LockerError` and changes nothing (the call stays the next one to undo).
- When there is nothing left to undo, `undo` raises `LockerError`.
- Undone calls are gone for good: they cannot be redone, and a later
  `undo` never reverses them again. A `store` or `retrieve` made after an
  `undo` becomes the most recent call.
- After an `undo`, the room is exactly as if the undone call had never
  been made: the same free lockers in the same order, the same takings, and
  later calls to `store` choose lockers as they would have then.

All existing behavior must keep working.
