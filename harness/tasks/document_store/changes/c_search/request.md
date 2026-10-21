Add text search to `docstore.py`.

- Add `DocumentStore.search(text, where="all", tag=None) -> list[str]`: the
  ids of the documents whose title or body contains `text`, in the order
  the documents were added. Matching ignores case, so `"monday"` matches
  `"Monday"` and `"MONDAY"`, and matches anywhere, including inside a word.
- `text` must be a non-empty string, or `ValueError` is raised.
- `where` chooses what is searched: `"title"` for titles only, `"body"` for
  bodies only, `"all"` for both. Any other value raises `ValueError`. A
  bad `text` is reported before a bad `where`.
- With `tag` given, only documents carrying that tag are considered, so an
  unused tag finds nothing.
- Searching reads the current body, so text removed by `update_body` no
  longer matches and text added by it does. Searching never changes a
  document.

All existing behavior must keep working.
