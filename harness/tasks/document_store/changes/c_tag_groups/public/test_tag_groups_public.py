"""Public checks for the c_tag_groups change (tag groups). Shown to the
editor, never to the writer.

Usage (with docstore.py importable, e.g. in the sandbox):
    python -m pytest changes/c_tag_groups/public/test_tag_groups_public.py
"""

import pytest
from docstore import DocumentStore


@pytest.fixture
def store():
    st = DocumentStore()
    st.add_document("notes", "Meeting notes", "Ship on Monday.")
    st.add_document("todo", "Things to do", "Buy milk.")
    st.add_document("post", "Blog post", "Hello world.")
    st.tag_document("notes", "final")
    st.tag_document("post", "draft")
    st.create_group("status")
    st.add_tag_to_group("status", "draft")
    st.add_tag_to_group("status", "final")
    return st


def test_documents_in_a_group_carry_one_of_its_tags(store):
    assert store.get_group_tags("status") == ["draft", "final"]
    assert store.get_documents_in_group("status") == ["notes", "post"]
    assert store.get_groups() == ["status"]


def test_tags_added_to_the_group_later_count(store):
    store.create_group("place")
    store.tag_document("todo", "home")
    assert store.get_documents_in_group("place") == []
    store.add_tag_to_group("place", "home")
    assert store.get_documents_in_group("place") == ["todo"]


def test_a_group_that_does_not_exist_raises_key_error(store):
    with pytest.raises(KeyError):
        store.get_documents_in_group("topic")
    with pytest.raises(KeyError):
        store.add_tag_to_group("topic", "home")
