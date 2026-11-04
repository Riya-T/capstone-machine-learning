# Wiki

Write a module `wiki.py` that keeps the pages of a small wiki. Every time
a page is written, the new text becomes a numbered revision, and the 5
latest revisions can be read back.

## Interface

```python
class WikiError(Exception): ...


class Wiki:
    def __init__(self): ...
    def create_page(self, page: str, author: str, text: str) -> None: ...
    def edit_page(self, page: str, author: str, text: str) -> None: ...
    def get_text(self, page: str) -> str: ...
    def get_history(self, page: str) -> list[tuple[int, str]]: ...
    def get_revision_count(self, page: str) -> int: ...
    def get_authors(self, page: str) -> list[str]: ...
    def get_pages(self) -> list[str]: ...
```

## Pages

- `create_page(page, author, text)` adds a page whose first revision is
  `text`, written by `author`. The text may be empty. It raises:
  - `ValueError` for an empty string or `None` as the page name or the
    author, or for a text that is not a string;
  - `WikiError` for a page name that already exists. The existing page is
    left as it was.
- `get_pages()` returns the names of all pages, in the order they were
  created.
- Every other method raises `KeyError` for a page name that does not
  exist. A page name that is not a `str`, such as `None` or `1`, counts as
  a page that does not exist.

## Revisions

- `edit_page(page, author, text)` adds a new revision with the given text,
  written by `author`. It raises:
  - `KeyError` for a page that does not exist;
  - `ValueError` for an empty string or `None` as the author, or for a text
    that is not a string;
  - `WikiError` for a text that is exactly the page's current text.
- Revisions of a page are numbered 1, 2, 3, … in the order they were
  written; the revision made by `create_page` is number 1.
- `get_text(page)` returns the text of the latest revision.
- `get_revision_count(page)` returns how many revisions were ever written
  to the page. That is also the number of its latest revision.
- `get_authors(page)` returns everyone who ever wrote a revision of the
  page, including revisions that `get_history` no longer lists, each name
  once, in any order. For example, if zoe writes revision
  1, bob revision 2 and zoe revision 3, `get_authors` returns `"zoe"` and
  `"bob"`.

## History: the 5 latest revisions

`get_history(page)` returns the page's 5 latest revisions as
`(number, text)` pairs, oldest first, or all of them if the page has
fewer than 5. Its last pair is always
`(get_revision_count(page), get_text(page))`.

For example, after `create_page("home", "ann", "v1")` and edits with the
texts `"v2"`, `"v3"`, … in that order:

| Revisions written | `get_history("home")` |
|---|---|
| 1 | `[(1, "v1")]` |
| 3 | `[(1, "v1"), (2, "v2"), (3, "v3")]` |
| 5 | `[(1, "v1"), (2, "v2"), (3, "v3"), (4, "v4"), (5, "v5")]` |
| 6 | `[(2, "v2"), (3, "v3"), (4, "v4"), (5, "v5"), (6, "v6")]` |
| 8 | `[(4, "v4"), (5, "v5"), (6, "v6"), (7, "v7"), (8, "v8")]` |

A failed call has no effect: if a method raises, every page, text and
revision is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when a call has several problems, the
order of the names from `get_authors`, other values that are not strings,
such as `7`, passed as an author or as the page name to `create_page`,
whether texts older than the 5 latest revisions are kept, what happens if
a returned list is changed, the text of error messages, saving the wiki to
a file, and use from several threads.
