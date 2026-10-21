"""Public checks for the c_trash change (trash and restore). Shown to the
editor, never to the writer.

Usage (with docstore.py importable, e.g. in the sandbox):
    python -m pytest changes/c_trash/public/test_trash_public.py
"""

import pytest
from docstore import DocumentStore, DocumentTrashed


@pytest.fixture
def store():
    st = DocumentStore()
    st.add_document("notes", "Meeting notes", "Ship on Monday.")
    st.add_document("todo", "Things to do", "Buy milk.")
    st.tag_document("notes", "work")
    return st


def test_a_trashed_document_disappears_from_the_listing(store):
    store.trash("notes")
    assert store.get_documents() == ["todo"]
    assert store.get_documents("work") == []
    assert store.get_trashed() == ["notes"]
    with pytest.raises(DocumentTrashed):
        store.get_body("notes")


def test_restore_brings_the_document_back_in_its_old_place(store):
    store.trash("notes")
    store.restore("notes")
    assert store.get_documents() == ["notes", "todo"]
    assert store.get_tags("notes") == ["work"]
    assert store.get_trashed() == []


def test_purge_deletes_trashed_documents_for_good(store):
    store.trash("todo")
    assert store.purge_trash() == ["todo"]
    with pytest.raises(KeyError):
        store.get_title("todo")
