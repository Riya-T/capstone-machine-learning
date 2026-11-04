When a page in `wiki.py` gets vandalised, we want to put it back to how it
was at an earlier revision and throw away everything written since.

- Add `Wiki.restore(page, number, expected_version=None)`. Revision
  `number`, which must be one of the revisions `get_history` lists, becomes
  the page's latest revision again, and every revision after it is
  discarded, as if it had never been written.
- After a restore, `get_text` returns the text of revision `number`,
  `get_revision_count` returns `number`, and the next edit gets the number
  `number + 1`. `get_history` lists revision `number` last, after the
  revisions before it that it listed before the restore. Whether it also
  lists older revisions again is unspecified. Once a new edit takes a
  discarded revision's number, the history shows the new text under that
  number.
- For example, with `Wiki(keep=3)` and a page whose history lists
  revisions 4, 5 and 6, `restore(page, 5)` gives a history that ends with
  revisions 4 and 5. The next edit adds a new revision 6 (history 4, 5,
  6), and the one after it adds revision 7 (history 5, 6, 7).
- `get_authors` no longer lists anyone whose only revisions were
  discarded. Authors of revisions that `get_history` no longer lists but
  that were not discarded are still listed, as before.
- A successful restore is a change to the page: its version goes up by 1.
  Versions never go down. `expected_version` works as in `edit_page`.

`restore` raises one of these, and then changes nothing:

- `KeyError` if there is no such page;
- `ValueError` for a revision number that is not an `int` of 1 or more;
- `VersionConflict` when `expected_version` does not match;
- `IndexError` for a revision that `get_history` does not list (higher
  than the latest one, or older than the history);
- `WikiError` when `number` is already the latest revision.

Which one is raised when several apply is unspecified.

All existing behavior must keep working.
