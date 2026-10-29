# Wiki

Write a module `wiki.py` that keeps the pages of a small wiki. Every time
a page is written, the new text becomes a numbered revision, and recent
revisions can be read back.

## Interface

```python
class WikiError(Exception): ...


class Wiki:
    def __init__(self): ...
    def create_page(self, page: str, author: str, text: str) -> None: ...
    def edit_page(self, page: str, author: str, text: str) -> None: ...
    def get_text(self, page: str) -> str: ...
    def get_revision(self, page: str, number: int) -> str: ...
    def get_revision_count(self, page: str) -> int: ...
    def get_authors(self, page: str) -> list[str]: ...
    def get_pages(self) -> list[str]: ...
```

## Pages

- `create_page(page, author, text)` adds a page whose first revision is
  `text`, written by `author`. The page name and the author must be
  non-empty strings, and the text must be a string, which may be empty;
  anything else raises `ValueError`. A page name that already exists raises
  `WikiError`, and the existing page is left as it was.
- `get_pages()` returns the names of all pages, in the order they were
  created.
- Every other method raises `KeyError` when given a page name that does not
  exist. A page name that is not a `str`, such as `None` or `1`, counts as
  a page that does not exist: it raises `KeyError`, not `ValueError`.

## Revisions

- `edit_page(page, author, text)` adds a new revision with the given text,
  written by `author`. The author and the text are checked like in
  `create_page`. An edit whose text is exactly the page's current text
  raises `WikiError`.
- Revisions of a page are numbered 1, 2, 3, … in the order they were
  written; the revision made by `create_page` is number 1.
- `get_text(page)` returns the text of the latest revision.
- `get_revision_count(page)` returns the number of revisions ever written
  to the page, including revisions that are no longer kept. It is not the
  number of revisions kept.
- `get_revision(page, number)` returns the text of revision `number`: the
  `number`-th revision ever written to the page, not the `number`-th one
  still kept. The number must be an `int` of 1 or more, or `ValueError` is
  raised. A number higher than the page's latest revision raises
  `IndexError`.
- `get_authors(page)` returns everyone who ever wrote a revision of the
  page, including revisions no longer kept, each name once, in the order
  of the first revision they wrote (not sorted). For example, if zoe
  writes revision 1, bob revision 2 and zoe revision 3, `get_authors`
  returns `["zoe", "bob"]`.

## Keeping only 5 revisions

Each page keeps the text of only its 5 most recent revisions:

1. After an edit, if the page has more than 5 revisions kept, the oldest
   kept revision is dropped and its text is forgotten.
2. `get_revision` for a dropped revision raises `IndexError`.
3. Dropping changes nothing else. Revision numbers stay the same,
   `get_revision_count` still counts every revision ever written, and the
   authors of dropped revisions stay in `get_authors`. So keep the count of
   revisions written separately from the revisions kept.

For example, after `create_page` and 7 edits a page has had 8 revisions:
`get_revision_count` returns 8, revisions 4 to 8 can be read by their
numbers, and `get_revision(page, 1)`, `2` and `3` raise `IndexError`.

When a call has several problems, `ValueError` for an invalid page name,
author, text or revision number is raised before `WikiError` or
`IndexError`.

A failed call has no effect: if a method raises, every page, text and
revision is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which of `KeyError` and `ValueError` is raised when a call has
both problems, `bool` revision numbers, what happens if a returned list is
changed, the text of error messages, saving the wiki to a file, and use from
several threads.
