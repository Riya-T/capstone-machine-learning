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
- `get_text(post_id)` returns the text of a post. An `int` that `post`
  never returned, such as 0, -1 or an id not used yet, raises `KeyError`.
- When the author is unknown and the text is invalid, `KeyError` is raised.

## Following

- `follow(follower, followee)` makes `follower` follow `followee`. Following
  is one-way: `followee` does not follow back.
- Following yourself raises `ValueError`, and following someone you already
  follow raises `FeedError`.
- `unfollow(follower, followee)` ends a follow. If `follower` does not follow
  `followee` it raises `FeedError`.
- `get_following(user)` returns the names `user` follows now, in the order
  they were followed (not sorted). Someone who is unfollowed and then
  followed again moves to the end.
- For `follow` and `unfollow`, `KeyError` comes first (for `follower`, then
  `followee`), before any `ValueError` or `FeedError`.

## Timeline

`get_timeline(user)` returns post ids in increasing order, which is oldest
first: every id from 1 up to the newest post, keeping only the posts written
by `user` or by a user that `user` follows now. The posts of different
authors are mixed by id, not grouped by author. Following someone brings in
all of their posts, also the ones written before the follow, and after an
unfollow none of that user's posts are in the timeline.

For example:

```python
feed = SocialFeed()
for name in ["ana", "ben", "cy"]:
    feed.add_user(name)

feed.post("ben", "hello")       # 1
feed.post("ana", "hi all")      # 2
feed.post("cy", "first!")       # 3
feed.post("ben", "lunch?")      # 4

feed.follow("ana", "cy")
feed.follow("ana", "ben")
feed.get_following("ana")       # ["cy", "ben"]: in the order followed
feed.get_timeline("ana")        # [1, 2, 3, 4]: her own posts and both others'
feed.get_timeline("ben")        # [1, 4]: ben follows nobody
feed.get_timeline("cy")         # [3]

feed.unfollow("ana", "cy")
feed.get_timeline("ana")        # [1, 2, 4]
feed.follow("ana", "cy")
feed.get_following("ana")       # ["ben", "cy"]: cy moved to the end
feed.get_timeline("ana")        # [1, 2, 3, 4]
```

A failed call has no effect: if a method raises, every timeline, every
following list and every text are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes:

- post ids that are not `int`s, such as `"1"`, `None` or `bool` values;
- which error `unfollow(name, name)` raises: `ValueError` or `FeedError`;
- names that are not strings passed to `add_user`;
- what happens if a returned list is changed, the text of error messages,
  saving the feed to a file, and use from several threads.
