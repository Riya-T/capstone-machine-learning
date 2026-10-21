Let authors in `feed.py` edit their posts, and refuse an edit that was made
from an out-of-date copy of the post.

- Add `SocialFeed.edit(post_id, text, expected_version=None)`, which
  replaces the text of a post. The new text must meet the same rules as the
  text of a new post, or `ValueError` is raised. The post keeps its id and
  its place in every timeline.
- Each post has a version number: 1 when it is posted, going up by 1 with
  every successful edit. Add `SocialFeed.get_version(post_id) -> int`.
- Add `class VersionConflict(FeedError)` to `feed.py`. When
  `expected_version` is given and is not the post's current version, `edit`
  raises `VersionConflict`. `None` means no check is made.
- Add `SocialFeed.get_revisions(post_id) -> list[str]`: every text the post
  has had, oldest first, ending with the current one.
- `edit`, `get_version` and `get_revisions` raise `KeyError` for an unknown
  post id. When an edit has several problems, they are reported in this
  order: `KeyError`, then `ValueError` for the text, then `VersionConflict`.
- A failed edit changes nothing: not the text, not the version, and not the
  revisions.

All existing behavior must keep working.
