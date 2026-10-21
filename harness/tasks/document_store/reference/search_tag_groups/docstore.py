"""Document store: titled text documents with tags, named groups of tags
and case-insensitive text search.

Correct solution for document_store after c_tag_groups and c_search.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from docstore import DocumentStore
    store = DocumentStore()
    store.add_document("d1", "Meeting notes", "Agreed to ship on Monday.")
    store.tag_document("d1", "work")
    store.create_group("area")
    store.add_tag_to_group("area", "work")
    store.get_documents_in_group("area")  # ["d1"]
    store.search("monday")  # ["d1"]
"""


class StoreError(Exception):
    pass


def check_text(value, what, allow_empty=False):
    if not isinstance(value, str) or (not value and not allow_empty):
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


SEARCH_FIELDS = ("title", "body", "all")


class DocumentStore:
    def __init__(self):
        self._titles = {}  # doc id -> title, in the order added
        self._bodies = {}  # doc id -> body
        self._tags = {}  # doc id -> list of tags, in the order added
        self._groups = {}  # group name -> list of tags, in the order added
        self._group_of = {}  # tag -> the group it belongs to

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
        if tag not in self._tags[doc_id]:
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

    # --- tag groups ---

    def create_group(self, group_name):
        check_text(group_name, "group name")
        if group_name in self._groups:
            raise StoreError(f"group {group_name!r} already exists")
        self._groups[group_name] = []

    def add_tag_to_group(self, group_name, tag):
        self._require_group(group_name)
        check_text(tag, "tag")
        owner = self._group_of.get(tag)
        if owner == group_name:
            return
        if owner is not None:
            raise StoreError(f"tag {tag!r} already belongs to group {owner!r}")
        self._groups[group_name].append(tag)
        self._group_of[tag] = group_name

    def get_group_tags(self, group_name):
        self._require_group(group_name)
        return list(self._groups[group_name])

    def get_groups(self):
        return list(self._groups)

    def get_documents_in_group(self, group_name):
        self._require_group(group_name)
        tags = self._groups[group_name]
        return [d for d in self.get_documents() if any(t in self._tags[d] for t in tags)]

    # --- search ---

    def search(self, text, where="all", tag=None):
        check_text(text, "search text")
        if where not in SEARCH_FIELDS:
            raise ValueError(f"where must be one of {SEARCH_FIELDS}, got {where!r}")
        needle = text.casefold()
        found = []
        for doc_id in self.get_documents(tag):
            fields = []
            if where in ("title", "all"):
                fields.append(self._titles[doc_id])
            if where in ("body", "all"):
                fields.append(self._bodies[doc_id])
            if any(needle in field.casefold() for field in fields):
                found.append(doc_id)
        return found

    def _require(self, doc_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(doc_id, str) or doc_id not in self._titles:
            raise KeyError(doc_id)

    def _require_group(self, group_name):
        if not isinstance(group_name, str) or group_name not in self._groups:
            raise KeyError(group_name)
