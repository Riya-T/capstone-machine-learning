"""Hidden tests for the initial document_store spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with docstore.py importable, e.g. in the sandbox):
    python -m pytest private/test_docstore_initial.py
"""

import pytest
from docstore import DocumentStore, StoreError

BAD_NAMES = ["", None, 7]
BAD_BODIES = [None, 7, ["text"]]


@pytest.fixture
def store():
    st = DocumentStore()
    st.add_document("notes", "Meeting notes", "We agreed to ship on Monday.")
    st.add_document("todo", "Things to do", "Buy milk.")
    st.add_document("draft", "Blog draft", "")
    return st


def state(st):
    """Every document's title, body and tags, to check that a failed call changed nothing."""
    return {d: (st.get_title(d), st.get_body(d), st.get_tags(d)) for d in st.get_documents()}


# --- documents --------------------------------------------------------------


def test_a_new_document_has_its_title_and_body_and_no_tags(store):
    assert store.get_title("todo") == "Things to do"
    assert store.get_body("todo") == "Buy milk."
    assert store.get_tags("todo") == []


def test_documents_are_listed_in_the_order_added():
    st = DocumentStore()
    for doc_id in ["zebra", "apple", "mango"]:
        st.add_document(doc_id, "t", "b")
    assert st.get_documents() == ["zebra", "apple", "mango"]


def test_the_body_may_be_empty_when_adding(store):
    assert store.get_body("draft") == ""
    assert store.get_documents() == ["notes", "todo", "draft"]


@pytest.mark.parametrize("bad_id", BAD_NAMES)
def test_invalid_ids_are_rejected(store, bad_id):
    before = state(store)
    with pytest.raises(ValueError):
        store.add_document(bad_id, "Title", "body")
    assert state(store) == before


@pytest.mark.parametrize("bad_title", BAD_NAMES)
def test_invalid_titles_are_rejected(store, bad_title):
    before = state(store)
    with pytest.raises(ValueError):
        store.add_document("fresh", bad_title, "body")
    assert state(store) == before
    with pytest.raises(KeyError):
        store.get_title("fresh")


@pytest.mark.parametrize("bad_body", BAD_BODIES)
def test_invalid_bodies_are_rejected_when_adding(store, bad_body):
    before = state(store)
    with pytest.raises(ValueError):
        store.add_document("fresh", "Title", bad_body)
    assert state(store) == before


def test_adding_an_existing_id_is_rejected_and_keeps_the_old_document(store):
    store.tag_document("notes", "work")
    before = state(store)
    with pytest.raises(StoreError):
        store.add_document("notes", "Other title", "other body")
    assert state(store) == before
    assert store.get_title("notes") == "Meeting notes"
    assert store.get_documents() == ["notes", "todo", "draft"]


@pytest.mark.parametrize(
    "call",
    [
        lambda st: st.update_body("missing", "x"),
        lambda st: st.tag_document("missing", "x"),
        lambda st: st.get_title("missing"),
        lambda st: st.get_body("missing"),
        lambda st: st.get_tags("missing"),
        lambda st: st.get_body(None),
        lambda st: st.get_tags(1),
    ],
)
def test_ids_not_in_the_store_raise_key_error(store, call):
    before = state(store)
    with pytest.raises(KeyError):
        call(store)
    assert state(store) == before


# --- bodies -----------------------------------------------------------------


def test_update_body_replaces_only_the_body(store):
    store.tag_document("todo", "home")
    store.update_body("todo", "Buy milk and bread.")
    assert store.get_body("todo") == "Buy milk and bread."
    assert store.get_title("todo") == "Things to do"
    assert store.get_tags("todo") == ["home"]


def test_update_body_may_set_an_empty_body(store):
    store.update_body("notes", "")
    assert store.get_body("notes") == ""


@pytest.mark.parametrize("bad_body", BAD_BODIES)
def test_invalid_bodies_are_rejected_when_updating(store, bad_body):
    before = state(store)
    with pytest.raises(ValueError):
        store.update_body("notes", bad_body)
    assert state(store) == before


def test_bodies_are_per_document(store):
    store.update_body("notes", "Changed.")
    assert store.get_body("todo") == "Buy milk."
    assert store.get_body("draft") == ""


# --- tags -------------------------------------------------------------------


def test_tags_are_listed_in_the_order_added(store):
    for tag in ["work", "2026", "agenda"]:
        store.tag_document("notes", tag)
    assert store.get_tags("notes") == ["work", "2026", "agenda"]


def test_adding_the_same_tag_twice_is_harmless(store):
    store.tag_document("notes", "work")
    store.tag_document("notes", "urgent")
    store.tag_document("notes", "work")
    assert store.get_tags("notes") == ["work", "urgent"]
    assert store.get_documents("work") == ["notes"]


@pytest.mark.parametrize("bad_tag", BAD_NAMES)
def test_invalid_tags_are_rejected(store, bad_tag):
    store.tag_document("notes", "work")
    before = state(store)
    with pytest.raises(ValueError):
        store.tag_document("notes", bad_tag)
    assert state(store) == before


def test_tags_are_per_document(store):
    store.tag_document("notes", "work")
    assert store.get_tags("todo") == []
    assert store.get_tags("draft") == []


# --- listing ----------------------------------------------------------------


def test_listing_by_tag_keeps_the_order_added(store):
    store.tag_document("draft", "writing")
    store.tag_document("notes", "writing")
    store.tag_document("todo", "home")
    assert store.get_documents("writing") == ["notes", "draft"]
    assert store.get_documents("home") == ["todo"]


def test_a_tag_nobody_carries_gives_an_empty_list(store):
    store.tag_document("notes", "work")
    assert store.get_documents("holiday") == []


def test_a_document_with_several_tags_is_listed_under_each(store):
    store.tag_document("notes", "work")
    store.tag_document("notes", "agenda")
    assert store.get_documents("work") == ["notes"]
    assert store.get_documents("agenda") == ["notes"]
    assert store.get_documents() == ["notes", "todo", "draft"]


# --- error order ------------------------------------------------------------


def test_an_invalid_title_or_body_is_reported_before_a_duplicate_id(store):
    with pytest.raises(ValueError):
        store.add_document("notes", "", "body")
    with pytest.raises(ValueError):
        store.add_document("notes", "Title", None)
    assert store.get_title("notes") == "Meeting notes"


def test_stores_do_not_share_documents():
    first, second = DocumentStore(), DocumentStore()
    first.add_document("a", "A", "body")
    assert second.get_documents() == []
    second.add_document("a", "Other", "")
    assert first.get_title("a") == "A"
    assert second.get_title("a") == "Other"
