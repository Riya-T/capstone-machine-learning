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
  exist, including values that are not strings at all, such as `None` or
  `1`.

## Revisions

- `edit_page(page, author, text)` adds a new revision with the given text,
  written by `author`. The author and the text are checked like in
  `create_page`. An edit whose text is exactly the page's current text
  raises `WikiError`.
- Revisions of a page are numbered 1, 2, 3, … in the order they were
  written; the revision made by `create_page` is number 1.
- `get_text(page)` returns the text of the latest revision.
- `get_revision_count(page)` returns the number of revisions the page has
  had so far.
- `get_revision(page, number)` returns the text of revision `number`. The
  number must be an `int` of 1 or more, or `ValueError` is raised. A number
  higher than the page's latest revision raises `IndexError`.
- Only the 5 most recent revisions of each page are kept. Asking for an
  older revision with `get_revision` raises `IndexError`. Revisions that
  are no longer kept still count for `get_revision_count` and
  `get_authors`.
- `get_authors(page)` returns everyone who wrote a revision of the page,
  each name once, in the order of the first revision they wrote.

When a call has several problems, the first of these is raised:

1. `KeyError` for a page that does not exist;
2. `ValueError` for an invalid page name, author, text or revision number;
3. `WikiError` or `IndexError`.

A failed call has no effect: if a method raises, every page, text and
revision is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` revision numbers, what happens if a returned list is
changed, the text of error messages, saving the wiki to a file, and use from
several threads.
