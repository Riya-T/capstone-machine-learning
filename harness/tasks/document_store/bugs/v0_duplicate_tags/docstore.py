"""Document store: titled text documents with tags.

Planted bug (initial version): tagging a document with a tag it already
has appends the tag again, so get_tags lists it twice. The public checks
never repeat a tag, so only the hidden initial tests catch it. Never shown
to the writer or the editor; validate-tasks checks that the tests catch it.

Usage:
    from docstore import DocumentStore
    store = DocumentStore()
    store.add_document("d1", "Meeting notes", "Agreed to ship on Monday.")
    store.tag_document("d1", "work")
"""


class StoreError(Exception):
    pass


def check_text(value, what, allow_empty=False):
    if not isinstance(value, str) or (not value and not allow_empty):
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


class DocumentStore:
    def __init__(self):
        self._titles = {}  # doc id -> title, in the order added
        self._bodies = {}  # doc id -> body
        self._tags = {}  # doc id -> list of tags, in the order added

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
        self._require(doc_id)
        check_text(body, "body", allow_empty=True)
        self._bodies[doc_id] = body

    def tag_document(self, doc_id, tag):
        self._require(doc_id)
        check_text(tag, "tag")
        self._tags[doc_id].append(tag)

    def get_title(self, doc_id):
        self._require(doc_id)
        return self._titles[doc_id]

    def get_body(self, doc_id):
        self._require(doc_id)
        return self._bodies[doc_id]

    def get_tags(self, doc_id):
        self._require(doc_id)
        return list(self._tags[doc_id])

    def get_documents(self, tag=None):
        if tag is None:
            return list(self._titles)
        return [doc_id for doc_id in self._titles if tag in self._tags[doc_id]]

    def _require(self, doc_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(doc_id, str) or doc_id not in self._titles:
            raise KeyError(doc_id)
