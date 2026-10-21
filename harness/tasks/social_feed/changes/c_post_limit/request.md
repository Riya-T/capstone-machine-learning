Make the 280-character limit on posts in `feed.py` adjustable, for the whole
feed and for single users.

- `SocialFeed` takes a new keyword argument `max_length=280`: the most
  characters a post may have. It must be an `int` of 1 or more (not
  `bool`), or `ValueError` is raised.
- `add_user` takes a new keyword argument `max_length=None`. `None` means
  the user goes by the feed's limit; an `int` of 1 or more (not `bool`)
  gives the user a limit of their own, which may be above or below the
  feed's. Anything else raises `ValueError` and no user is added. An
  invalid limit is reported before a name that was already added.
- Add `SocialFeed.get_max_length(user) -> int`: the limit that applies to
  the user's next post. It raises `KeyError` for a user that was not added.
- Add `SocialFeed.set_max_length(user, max_length)`: replaces the user's own
  limit, with the same rules as in `add_user`; `None` puts the user back on
  the feed's limit. It raises `KeyError` for a user that was not added, then
  `ValueError` for an invalid limit, and in either case changes nothing.
- `post` raises `ValueError` for a text longer than the author's limit.
  Posts that already exist are never affected when a limit changes later.

If both the name and the limit passed to `add_user` are invalid, either
`ValueError` may come first. All existing behavior must keep working.
