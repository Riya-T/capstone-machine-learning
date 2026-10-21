"""Hidden tests for the c_search change (text search). Never shown to the
writer or the editor.

Usage (with docstore.py importable, e.g. in the sandbox):
    python -m pytest changes/c_search/private/test_search_new.py
"""

import pytest
from docstore import DocumentStore


@pytest.fixture
def store():
    st = DocumentStore()
    st.add_document("notes", "Meeting notes", "We agreed to ship on Monday.")
    st.add_document("todo", "Things to do", "Buy milk before Monday.")
    st.add_document("post", "Monday blues", "Hello world.")
    st.add_document("blank", "Untitled", "")
    st.tag_document("notes", "work")
    st.tag_document("post", "work")
    st.tag_document("todo", "home")
    return st


def test_matches_in_either_title_or_body_count(store):
    assert store.search("Monday") == ["notes", "todo", "post"]
    assert store.search("world") == ["post"]
    assert store.search("Meeting") == ["notes"]
    assert store.search("friday") == []


def test_results_follow_the_order_documents_were_added():
    st = DocumentStore()
    for doc_id in ["c", "a", "b"]:
        st.add_document(doc_id, "Shared word", "")
    assert st.search("shared") == ["c", "a", "b"]


def test_matching_ignores_case_in_both_directions(store):
    assert store.search("mOnDaY") == ["notes", "todo", "post"]
    assert store.search("HELLO") == ["post"]
    assert store.search("untitled") == ["blank"]


def test_matching_works_inside_a_word(store):
    assert store.search("agree") == ["notes"]
    assert store.search("ilk") == ["todo"]


def test_a_document_is_listed_once_even_if_title_and_body_match():
    st = DocumentStore()
    st.add_document("d", "Monday plan", "Plan for Monday.")
    assert st.search("monday") == ["d"]


def test_where_limits_the_search_to_titles_or_bodies(store):
    assert store.search("Monday", where="title") == ["post"]
    assert store.search("milk", where="title") == []
    assert store.search("Monday", where="body") == ["notes", "todo"]
    assert store.search("blues", where="body") == []
    assert store.search("Monday", where="all") == ["notes", "todo", "post"]


def test_search_can_be_restricted_to_a_tag(store):
    assert store.search("Monday", tag="work") == ["notes", "post"]
    assert store.search("Monday", tag="home") == ["todo"]
    assert store.search("Monday", where="body", tag="work") == ["notes"]
    assert store.search("Monday", tag="holiday") == []


def test_search_sees_body_updates(store):
    store.update_body("post", "Nothing here.")
    assert store.search("world") == []
    assert store.search("nothing") == ["post"]
    assert store.search("Monday") == ["notes", "todo", "post"]  # title still matches


@pytest.mark.parametrize("bad_text", ["", None, 5])
def test_invalid_search_text_is_rejected(store, bad_text):
    with pytest.raises(ValueError):
        store.search(bad_text)


@pytest.mark.parametrize("bad_where", ["everywhere", "", None, 3, "Title"])
def test_invalid_where_values_are_rejected(store, bad_where):
    with pytest.raises(ValueError):
        store.search("Monday", where=bad_where)


def test_bad_text_and_bad_where_together_still_raise_value_error(store):
    with pytest.raises(ValueError):
        store.search("", where="everywhere")
    with pytest.raises(ValueError):
        store.search(None, where=None)


def test_searching_changes_no_document(store):
    store.search("monday")
    store.search("HELLO", where="body", tag="work")
    assert store.get_title("post") == "Monday blues"
    assert store.get_body("notes") == "We agreed to ship on Monday."
    assert store.get_tags("notes") == ["work"]
