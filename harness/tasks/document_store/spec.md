# Document store

Write a module `docstore.py` that keeps short text documents, each with a
title, a body and any number of tags.

## Interface

```python
class StoreError(Exception): ...


class DocumentStore:
    def __init__(self): ...
    def add_document(self, doc_id: str, title: str, body: str) -> None: ...
    def update_body(self, doc_id: str, body: str) -> None: ...
    def tag_document(self, doc_id: str, tag: str) -> None: ...
    def get_title(self, doc_id: str) -> str: ...
    def get_body(self, doc_id: str) -> str: ...
    def get_tags(self, doc_id: str) -> list[str]: ...
    def get_documents(self, tag: str | None = None) -> list[str]: ...
```

## Documents

- `add_document(doc_id, title, body)` adds a document with no tags. The id
  and the title must be non-empty strings, and the body must be a string,
  which may be empty; anything else raises `ValueError`. An id that is
  already in the store raises `StoreError`, and the stored document is left
  as it was.
- Every other method raises `KeyError` when given an id that is not in the
  store, including values that are not strings at all, such as `None` or
  `1`.
- `get_title(doc_id)` and `get_body(doc_id)` return the title and the body
  exactly as they were given.
- `update_body(doc_id, body)` replaces the body. A body that is not a
  string raises `ValueError`. The title and the tags are not affected.

## Tags

- `tag_document(doc_id, tag)` adds a tag to a document. A tag that is empty
  or not a string raises `ValueError`. Adding a tag the document already
  has does nothing.
- `get_tags(doc_id)` returns the document's tags in the order they were
  added.

## Listing

- `get_documents()` returns the ids of all documents, in the order they
  were added.
- `get_documents(tag)` returns only the ids of the documents that carry
  that tag, in the same order. A tag that no document carries gives `[]`.

When `add_document` has several problems, `ValueError` for an invalid id,
title or body is raised before `StoreError` for an id that is already in
the store.

A failed call has no effect: if a method raises, no document, body or tag
changes.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which of `KeyError` and `ValueError` is raised when a call has
both problems, tags passed to `get_documents` that are not strings, what happens
if a returned list is changed, the text of error messages, saving the store
to a file, and use from several threads.
