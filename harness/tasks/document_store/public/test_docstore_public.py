"""Public checks for docstore.py.

Usage (with docstore.py importable, e.g. in the sandbox):
    python -m pytest public/test_docstore_public.py
"""

import pytest
from docstore import DocumentStore


@pytest.fixture
def store():
    st = DocumentStore()
    st.add_document("notes", "Meeting notes", "We agreed to ship on Monday.")
    st.add_document("todo", "Things to do", "Buy milk.")
    return st


def test_title_and_body_are_stored_as_given(store):
    assert store.get_title("notes") == "Meeting notes"
    assert store.get_body("notes") == "We agreed to ship on Monday."
    assert store.get_tags("notes") == []


def test_an_empty_body_is_allowed(store):
    store.add_document("blank", "Empty page", "")
    assert store.get_body("blank") == ""
    store.update_body("todo", "")
    assert store.get_body("todo") == ""


def test_tags_keep_the_order_they_were_added(store):
    store.tag_document("notes", "work")
    store.tag_document("notes", "2026")
    assert store.get_tags("notes") == ["work", "2026"]


def test_documents_can_be_listed_by_tag(store):
    store.tag_document("todo", "home")
    assert store.get_documents() == ["notes", "todo"]
    assert store.get_documents("home") == ["todo"]
    assert store.get_documents("work") == []


def test_unknown_document_raises_key_error(store):
    with pytest.raises(KeyError):
        store.get_body("missing")


def test_an_empty_tag_raises_value_error(store):
    with pytest.raises(ValueError):
        store.tag_document("notes", "")
