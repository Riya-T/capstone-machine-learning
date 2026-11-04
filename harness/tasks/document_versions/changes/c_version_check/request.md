Two people editing the same page in `wiki.py` can overwrite each other's
work without noticing. Give every page a version number so an editor can
say which version their edit was based on.

- Each page has a version. It is 1 when the page is created and goes up by
  1 with every successful change to the page. A failed call never changes
  it.
- Add `Wiki.get_version(page) -> int`. It raises `KeyError` for a page that
  does not exist.
- `edit_page` takes a new keyword argument `expected_version=None`. When it
  is `None`, the edit works as before. Otherwise, if it is not equal to the
  page's current version, the edit raises `VersionConflict` and changes
  nothing.
- Add `class VersionConflict(WikiError)` to `wiki.py`.

When an edit whose `expected_version` does not match also has another
problem (no such page, an invalid author or text, or a text that does not
change), which error is raised is unspecified.

All existing behavior must keep working.
