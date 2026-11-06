Add a trash to `docstore.py`, so a document can be removed and brought back
later, or thrown away for good.

- Add `class DocumentTrashed(StoreError)` to `docstore.py`.
- Add `DocumentStore.trash(doc_id)`: moves the document to the trash. It
  raises `KeyError` for an id that is not in the store and
  `DocumentTrashed` if the document is already in the trash.
- Add `DocumentStore.restore(doc_id)`: brings a trashed document back with
  its title, body and tags exactly as they were. It keeps its original
  place in `get_documents`, which stays in the order documents were added.
  It raises `KeyError` for an id that is not in the store and `StoreError`
  if the document is not in the trash.
- Add `DocumentStore.get_trashed() -> list[str]`: the ids in the trash, in
  the order they were trashed. A document that is restored and trashed
  again goes to the end.
- While a document is in the trash, `get_documents` leaves it out, with or
  without a tag, and `get_title`, `get_body`, `get_tags`, `update_body` and
  `tag_document` raise `DocumentTrashed`. `add_document` with its id still
  raises `StoreError`, since the id is in use.
- Add `DocumentStore.purge_trash() -> list[str]`: deletes every document
  in the trash for good and returns their ids in trash order. Afterwards
  those ids are not in the store (`KeyError`) and may be used again by
  `add_document` for a fresh document with no tags.
- A trashed document is still in the store until `purge_trash` deletes
  it. So `trash` on a document that is already in the trash raises
  `DocumentTrashed`, not `KeyError`, and `restore` on a document that is
  in the store but not in the trash raises `StoreError`, not `KeyError`.
  `KeyError` is only for ids that were never added or were purged.

When a call on a trashed document also has an invalid body or tag, which
of `DocumentTrashed` and `ValueError` is raised is unspecified. A failed
call changes nothing. All existing behavior must keep working.
