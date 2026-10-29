# Chat rooms

Write a module `chat.py` that keeps the users of a chat service, the rooms
they have joined and the messages posted in each room.

## Interface

```python
class ChatError(Exception): ...


class ChatServer:
    def __init__(self): ...
    def add_user(self, username: str) -> None: ...
    def join(self, username: str, room: str) -> None: ...
    def leave(self, username: str, room: str) -> None: ...
    def post(self, username: str, room: str, text: str) -> None: ...
    def get_members(self, room: str) -> list[str]: ...
    def get_messages(self, room: str) -> list[tuple[str, str]]: ...
    def get_rooms(self) -> list[str]: ...
```

## Users

- `add_user(username)` adds a user who is in no room. The username must be
  a non-empty `str`, or `ValueError` is raised. Adding a username that is
  already added raises `ChatError`.
- `join`, `leave` and `post` raise `KeyError` when given a username that
  was never added. A username that is not a `str`, such as `None` or `1`,
  counts as never added: it raises `KeyError`, not `ValueError`.

## Rooms

- `join(username, room)` makes the user a member of the room. The room name
  must be a non-empty `str`, or `ValueError` is raised. A room is created
  the first time someone joins it, with that user as its only member and no
  messages. If the user is already a member of that room, `ChatError` is
  raised; this is checked after the user and the room name.
- `leave(username, room)` removes the user from the room. A room that
  nobody is a member of still exists and keeps its messages. If the user is
  not a member of that room, `ChatError` is raised.
- `get_members(room)` returns the room's members, in the order they joined
  (a user who leaves and joins again goes to the end).
- `get_rooms()` returns every room, in the order the rooms were created.
- `leave`, `post`, `get_members` and `get_messages` raise `KeyError` for a
  room that was never created. A room that is not a `str`, such as `None`
  or `3`, counts as never created there (only `join` raises `ValueError`
  for a bad room name).
  Where a user and a room are both given, the user is checked first.

## Messages

- `post(username, room, text)` adds a message to the room. The text must
  be a non-empty `str`, or `ValueError` is raised. Only a member of the room
  can post; anyone else gets `ChatError`, which is checked last.
- `get_messages(room)` returns the room's messages, oldest first, as
  `(username, text)` tuples. A room nobody has posted in gives an empty
  list. Messages stay after their author leaves.

A failed call has no effect: if a method raises, every room, every list of
members and every list of messages is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which of `KeyError` and `ValueError` is raised when a call has
both problems, what happens if a returned list is changed, the text of error
messages, saving the chat to a file, and use from several threads.
