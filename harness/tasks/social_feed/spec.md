# Social feed

Write a module `feed.py` for a small social network: users write short
posts, follow each other, and read a timeline of the posts they care about.

## Interface

```python
class FeedError(Exception): ...


class SocialFeed:
    def __init__(self): ...
    def add_user(self, name: str) -> None: ...
    def post(self, author: str, text: str) -> int: ...
    def get_text(self, post_id: int) -> str: ...
    def follow(self, follower: str, followee: str) -> None: ...
    def unfollow(self, follower: str, followee: str) -> None: ...
    def get_following(self, user: str) -> list[str]: ...
    def get_timeline(self, user: str) -> list[int]: ...
```

## Users

- `add_user(name)` adds a user who follows nobody and has written nothing.
  An empty name raises `ValueError`, and a name that was already added
  raises `FeedError`.
- Every other method that takes a user raises `KeyError` for a name that
  was not added, including values that are not strings at all, such as
  `None` or `1`.

## Posts

- `post(author, text)` stores a post and returns its id. Ids are `int`s:
  the first post in the feed gets 1, the next one 2, and so on, counting
  the posts of all users together. A call that raises does not use up an id.
- The text must be a string of 1 to 280 characters; anything else (the
  empty string, a longer string, a value that is not a string) raises
  `ValueError`.
- `get_text(post_id)` returns the text of a post. An id that `post` never
  returned raises `KeyError`.
- When the author is unknown and the text is invalid, `KeyError` is raised.

## Following

- `follow(follower, followee)` makes `follower` follow `followee`. Following
  is one-way: `followee` does not follow back.
- Following yourself raises `ValueError`, and following someone you already
  follow raises `FeedError`.
- `unfollow(follower, followee)` ends a follow. If `follower` does not follow
  `followee` it raises `FeedError`.
- `get_following(user)` returns the names `user` follows now, in the order
  they were followed. Someone who is unfollowed and then followed again
  moves to the end.
- For `follow` and `unfollow`, `KeyError` comes first (for `follower`, then
  `followee`), then `ValueError`, then `FeedError`.

## Timeline

`get_timeline(user)` returns the ids of the posts written by `user` and by
every user that `user` follows now, oldest first. Posts written before the
follow are included, and after an unfollow that user's posts are no longer
in the timeline.

A failed call has no effect: if a method raises, every timeline, every
following list and every text are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_user`, `bool` post ids,
what happens if a returned list is changed, the text of error messages,
saving the feed to a file, and use from several threads.
