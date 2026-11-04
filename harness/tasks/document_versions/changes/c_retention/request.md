Some pages in `wiki.py` need a longer history than others. Make the number
of revisions that `get_history` returns adjustable instead of always 5.

- `Wiki` takes a new keyword argument `keep=5`: how many of the latest
  revisions `get_history` returns for each page. It must be an `int` of 1
  or more; anything else raises `ValueError`.
- `create_page` takes a new keyword argument `keep=None`. `None` means the
  page uses the wiki's `keep`. Otherwise it must be an `int` of 1 or more
  and sets the limit for that page alone; anything else raises
  `ValueError` and no page is created. Which error is raised when an
  invalid `keep` is given for a page name that already exists is
  unspecified.
- Add `Wiki.get_keep(page) -> int`, which returns the limit that applies to
  the page. It raises `KeyError` for a page that does not exist.
- `get_history` now returns the page's latest revisions up to the page's
  own limit instead of 5. For example, with `Wiki(keep=2)`, after a page's
  revisions 1, 2 and 3 are written, `get_history` returns revisions 2 and
  3. Nothing else changes: `get_revision_count` and `get_authors` still
  count every revision, as before.

All existing behavior must keep working.
