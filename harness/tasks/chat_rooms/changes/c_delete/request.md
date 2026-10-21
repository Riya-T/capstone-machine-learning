Let messages be deleted in `chat.py`.

- `post` now returns the new message's id: an `int` that is 1 for the first
  message posted on the server and goes up by 1 with every later message,
  whatever the room. An id is never given out twice, even after a deletion.
- Add `ChatServer.delete_message(message_id)`, which removes that message
  from its room: `get_messages` no longer returns it, and the other
  messages keep their order. It raises `KeyError` if no message was ever
  posted with that id (including values that are not ints), then
  `ChatError` if the message was already deleted. In each case nothing
  changes.
- Add `ChatServer.get_message_ids(room) -> list[int]`: the ids of the
  messages still in the room, oldest first. It raises `KeyError` for an
  unknown room.

All existing behavior must keep working.
