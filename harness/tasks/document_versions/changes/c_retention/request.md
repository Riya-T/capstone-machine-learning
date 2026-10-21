Some pages in `wiki.py` need a longer history than others. Make the number
of revisions kept per page adjustable instead of always 5.

- `Wiki` takes a new keyword argument `keep=5`: how many of the most recent
  revisions each page keeps. It must be an `int` of 1 or more (not a
  `bool`); anything else raises `ValueError`.
- `create_page` takes a new keyword argument `keep=None`. `None` means the
  page uses the wiki's `keep`. Otherwise it must be an `int` of 1 or more
  (not a `bool`) and sets the limit for that page alone; anything else
  raises `ValueError` and no page is created. An invalid `keep` counts as
  an invalid argument, so it is reported before `WikiError` for a page name
  that already exists.
- Add `Wiki.get_keep(page) -> int`, which returns the limit that applies to
  the page. It raises `KeyError` for a page that does not exist.
- Everything that used the fixed limit of 5 now uses the page's own limit:
  `get_revision` raises `IndexError` for a revision that is no longer kept
  under that limit, and revisions that are no longer kept still count
  everywhere else, as before.

All existing behavior must keep working.
