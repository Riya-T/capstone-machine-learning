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

When `edit_page` has several problems, the first of these is raised:

1. `KeyError` if there is no such page;
2. `ValueError` for an invalid author or text;
3. `VersionConflict`;
4. `WikiError` for an edit that does not change the text.

All existing behavior must keep working.
