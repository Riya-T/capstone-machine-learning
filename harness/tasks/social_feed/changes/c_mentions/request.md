Let users in `feed.py` find the posts that mention them.

- A post mentions a user when one of the words of its text, splitting the
  text on whitespace, is exactly `@` followed by the user's name. So
  `"hi @ana"` mentions `ana`, but `"hi @ana!"`, `"@Ana"`, `"@an"` and
  `"mail@ana"` do not.
- Mentions are worked out from the users that exist when they are asked
  for: a post that names someone who only joins later counts as mentioning
  them once they have joined.
- Add `SocialFeed.get_mentions(user) -> list[int]`: the ids of the posts
  that mention `user`, oldest first, leaving out posts written by users
  that `user` has blocked. A post that mentions the user more than once is
  listed once, and users can mention themselves. It raises `KeyError` for a
  user that was not added.
- `get_mentions` takes a keyword argument `author=None`. When it is given,
  only posts written by that user are listed; it raises `KeyError` for an
  author that was not added.
- Add `SocialFeed.get_mentioned(post_id) -> list[str]`: the users the post
  mentions, in the order they are first mentioned in its text. It raises
  `KeyError` for an unknown post id.

All existing behavior must keep working.
