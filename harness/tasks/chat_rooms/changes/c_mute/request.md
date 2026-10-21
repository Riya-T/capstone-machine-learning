Let moderators mute a user in `chat.py`, so the user can read but not post.

- Add `class UserMuted(ChatError)` to `chat.py`.
- Add `ChatServer.mute(username)`, `ChatServer.unmute(username)` and
  `ChatServer.is_muted(username) -> bool`. All three raise `KeyError` for a
  username that was never added. New users are not muted. Muting a muted
  user, or unmuting one who is not muted, does nothing.
- While a user is muted, `post` by that user raises `UserMuted` in every
  room and changes nothing. Joining and leaving rooms still work, and the
  user's earlier messages stay where they are.
- In `post`, `UserMuted` is checked last: after every `KeyError` and
  `ValueError` check and after the check that the user is a member of the
  room.
- Muting and unmuting add nothing to any room's messages or members.

All existing behavior must keep working.
