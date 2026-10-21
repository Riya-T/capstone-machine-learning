Add ways to search the messages in `chat.py`.

- `get_messages` takes two new keyword arguments, `by=None` and
  `containing=None`. With `by` given, only messages posted by that user are
  returned; with `containing` given, only messages whose text contains that
  string (exact, case-sensitive substring match). Both may be combined. The
  result keeps the usual order, oldest first.
- `get_messages` raises `KeyError` for an unknown room, then `KeyError` if
  `by` is neither `None` nor a username that was added, then `ValueError`
  if `containing` is neither `None` nor a `str`.
- Add `ChatServer.get_posts(username) -> list[tuple[str, str]]`: every
  message the user has posted in any room, oldest first across all rooms,
  as `(room, text)` tuples. It raises `KeyError` for a username that was
  never added.

All existing behavior must keep working.
