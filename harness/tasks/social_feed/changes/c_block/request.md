Let users in `feed.py` block each other.

- Add `SocialFeed.block(user, other)`, `SocialFeed.unblock(user, other)` and
  `SocialFeed.is_blocked(user, other) -> bool`, which tells whether `user`
  has blocked `other`. All three raise `KeyError` for a user that was not
  added (`user` is checked before `other`), and `block` raises `ValueError`
  when `user` and `other` are the same. Blocking someone who is already
  blocked, or unblocking someone who is not, does nothing.
- Add `SocialFeed.get_blocked(user) -> list[str]`: the users that `user` has
  blocked, in the order they were blocked. It raises `KeyError` for a user
  that was not added.
- Add `class Blocked(FeedError)` to `feed.py`.
- Blocking ends every follow between the two users, in both directions.
- As long as either of two users has blocked the other, `follow` between
  them, in either direction, raises `Blocked` and changes nothing. This
  check comes after the `KeyError` and `ValueError` checks of `follow`.
- Unblocking does not bring back follows that the block ended. Blocking
  does not delete or hide any post, and blocked users can still post.

All existing behavior must keep working.
