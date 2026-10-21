"""Public checks for the c_search change (text search). Shown to the editor,
never to the writer.

Usage (with docstore.py importable, e.g. in the sandbox):
    python -m pytest changes/c_search/public/test_search_public.py
"""

import pytest
from docstore import DocumentStore


@pytest.fixture
def store():
    st = DocumentStore()
    st.add_document("notes", "Meeting notes", "We agreed to ship on Monday.")
    st.add_document("todo", "Things to do", "Buy milk before Monday.")
    st.add_document("post", "Monday blues", "Hello world.")
    return st


def test_search_finds_text_in_titles_and_bodies(store):
    assert store.search("Monday") == ["notes", "todo", "post"]
    assert store.search("milk") == ["todo"]
    assert store.search("friday") == []


def test_search_ignores_case(store):
    assert store.search("MONDAY") == ["notes", "todo", "post"]
    assert store.search("hello") == ["post"]


def test_search_can_be_limited_to_titles_or_bodies(store):
    assert store.search("Monday", where="title") == ["post"]
    assert store.search("Monday", where="body") == ["notes", "todo"]


def test_an_empty_search_text_raises_value_error(store):
    with pytest.raises(ValueError):
        store.search("")
