When a page in `wiki.py` gets vandalised, we want to put it back to how it
was at an earlier revision and throw away everything written since.

- Add `Wiki.restore(page, number, expected_version=None)`. Revision
  `number` becomes the page's latest revision again, and every revision
  after it is discarded, as if it had never been written.
- After a restore, `get_text` returns the text of revision `number`,
  `get_revision_count` returns `number`, and the next edit gets the number
  `number + 1`. A discarded revision can no longer be read; once a new edit
  takes its number, `get_revision` returns the new text.
- `get_authors` no longer lists anyone whose only revisions were
  discarded. Authors of revisions that are no longer kept but were not
  discarded are still listed, as before.
- Restoring never brings back a revision that was already no longer kept:
  such a revision stays unreadable, and the page keeps at most as many
  revisions as its limit, counting from its new latest revision.
- A successful restore is a change to the page: its version goes up by 1.
  Versions never go down. `expected_version` works as in `edit_page`.

When `restore` has several problems, the first of these is raised, and
nothing changes:

1. `KeyError` if there is no such page;
2. `ValueError` for a revision number that is not an `int` of 1 or more;
3. `VersionConflict`;
4. `IndexError` for a revision that is higher than the latest one or is no
   longer kept;
5. `WikiError` when `number` is already the latest revision.

All existing behavior must keep working.
