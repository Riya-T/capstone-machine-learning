"""Document store: titled text documents with tags, and a trash to remove
documents and bring them back.

Correct solution for document_store after c_trash.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from docstore import DocumentStore
    store = DocumentStore()
    store.add_document("d1", "Meeting notes", "Agreed to ship on Monday.")
    store.tag_document("d1", "work")
    store.trash("d1")
    store.restore("d1")
"""


class StoreError(Exception):
    pass


class DocumentTrashed(StoreError):
    pass


def check_text(value, what, allow_empty=False):
    if not isinstance(value, str) or (not value and not allow_empty):
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


class DocumentStore:
    def __init__(self):
        self._titles = {}  # doc id -> title, in the order added
        self._bodies = {}  # doc id -> body
        self._tags = {}  # doc id -> list of tags, in the order added
        self._trashed = []  # ids in the trash, in the order trashed

    def add_document(self, doc_id, title, body):
        check_text(doc_id, "doc_id")
        check_text(title, "title")
        check_text(body, "body", allow_empty=True)
        if doc_id in self._titles:
            raise StoreError(f"document {doc_id!r} already exists")
        self._titles[doc_id] = title
        self._bodies[doc_id] = body
        self._tags[doc_id] = []

    def update_body(self, doc_id, body):
        self._require_live(doc_id)
        check_text(body, "body", allow_empty=True)
        self._bodies[doc_id] = body

    def tag_document(self, doc_id, tag):
        self._require_live(doc_id)
        check_text(tag, "tag")
        if tag not in self._tags[doc_id]:
            self._tags[doc_id].append(tag)

    def get_title(self, doc_id):
        self._require_live(doc_id)
        return self._titles[doc_id]

    def get_body(self, doc_id):
        self._require_live(doc_id)
        return self._bodies[doc_id]

    def get_tags(self, doc_id):
        self._require_live(doc_id)
        return list(self._tags[doc_id])

    def get_documents(self, tag=None):
        live = [doc_id for doc_id in self._titles if doc_id not in self._trashed]
        if tag is None:
            return live
        return [doc_id for doc_id in live if tag in self._tags[doc_id]]

    # --- trash ---

    def trash(self, doc_id):
        self._require_live(doc_id)
        self._trashed.append(doc_id)

    def restore(self, doc_id):
        self._require(doc_id)
        if doc_id not in self._trashed:
            raise StoreError(f"document {doc_id!r} is not in the trash")
        self._trashed.remove(doc_id)

    def get_trashed(self):
        return list(self._trashed)

    def purge_trash(self):
        purged = self._trashed
        self._trashed = []
        for doc_id in purged:
            del self._titles[doc_id]
            del self._bodies[doc_id]
            del self._tags[doc_id]
        return purged

    def _require(self, doc_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(doc_id, str) or doc_id not in self._titles:
            raise KeyError(doc_id)

    def _require_live(self, doc_id):
        self._require(doc_id)
        if doc_id in self._trashed:
            raise DocumentTrashed(f"document {doc_id!r} is in the trash")
