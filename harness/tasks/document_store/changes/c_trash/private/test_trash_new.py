"""Hidden tests for the c_trash change (trash and restore). Never shown to
the writer or the editor.

Usage (with docstore.py importable, e.g. in the sandbox):
    python -m pytest changes/c_trash/private/test_trash_new.py
"""

import pytest
from docstore import DocumentStore, DocumentTrashed, StoreError


@pytest.fixture
def store():
    st = DocumentStore()
    st.add_document("notes", "Meeting notes", "Ship on Monday.")
    st.add_document("todo", "Things to do", "Buy milk.")
    st.add_document("post", "Blog post", "Hello world.")
    st.tag_document("notes", "work")
    st.tag_document("todo", "home")
    st.tag_document("post", "work")
    return st


def live_state(st):
    return {d: (st.get_title(d), st.get_body(d), st.get_tags(d)) for d in st.get_documents()}


def test_trashed_documents_are_left_out_of_every_listing(store):
    store.trash("notes")
    assert store.get_documents() == ["todo", "post"]
    assert store.get_documents("work") == ["post"]
    assert store.get_documents("home") == ["todo"]


@pytest.mark.parametrize(
    "call",
    [
        lambda st: st.get_title("notes"),
        lambda st: st.get_body("notes"),
        lambda st: st.get_tags("notes"),
        lambda st: st.update_body("notes", "changed"),
        lambda st: st.tag_document("notes", "late"),
        lambda st: st.trash("notes"),
    ],
)
def test_a_trashed_document_cannot_be_read_changed_or_trashed_again(store, call):
    store.trash("notes")
    before = live_state(store)
    with pytest.raises(DocumentTrashed):
        call(store)
    assert live_state(store) == before
    assert store.get_trashed() == ["notes"]


def test_restore_brings_back_title_body_and_tags_unchanged(store):
    store.update_body("notes", "Ship on Tuesday.")
    store.tag_document("notes", "urgent")
    store.trash("notes")
    store.restore("notes")
    assert store.get_title("notes") == "Meeting notes"
    assert store.get_body("notes") == "Ship on Tuesday."
    assert store.get_tags("notes") == ["work", "urgent"]
    assert store.get_documents("work") == ["notes", "post"]


def test_a_restored_document_keeps_its_original_place(store):
    store.trash("notes")
    store.add_document("memo", "Memo", "")
    store.restore("notes")
    assert store.get_documents() == ["notes", "todo", "post", "memo"]
    store.trash("todo")
    store.restore("todo")
    assert store.get_documents() == ["notes", "todo", "post", "memo"]


def test_trashed_ids_are_listed_in_trash_order(store):
    assert store.get_trashed() == []
    assert store.purge_trash() == []
    assert store.get_documents() == ["notes", "todo", "post"]
    store.trash("post")
    store.trash("notes")
    assert store.get_trashed() == ["post", "notes"]
    store.restore("post")
    assert store.get_trashed() == ["notes"]
    store.trash("post")
    assert store.get_trashed() == ["notes", "post"]


def test_restoring_a_document_that_is_not_trashed_raises_store_error(store):
    before = live_state(store)
    with pytest.raises(StoreError):
        store.restore("notes")
    assert live_state(store) == before
    assert store.get_trashed() == []


@pytest.mark.parametrize(
    "call",
    [
        lambda st: st.trash("missing"),
        lambda st: st.restore("missing"),
        lambda st: st.trash(None),
        lambda st: st.restore(3),
    ],
)
def test_trash_and_restore_reject_ids_not_in_the_store(store, call):
    before = live_state(store)
    with pytest.raises(KeyError):
        call(store)
    assert live_state(store) == before
    assert store.get_trashed() == []


def test_a_trashed_id_is_still_in_use(store):
    store.trash("notes")
    with pytest.raises(StoreError):
        store.add_document("notes", "New notes", "")
    store.restore("notes")
    assert store.get_title("notes") == "Meeting notes"


def test_purge_returns_the_trash_in_order_and_forgets_the_documents(store):
    store.trash("post")
    store.trash("notes")
    assert store.purge_trash() == ["post", "notes"]
    assert store.get_trashed() == []
    assert live_state(store) == {"todo": ("Things to do", "Buy milk.", ["home"])}
    for doc_id in ["post", "notes"]:
        with pytest.raises(KeyError):
            store.get_title(doc_id)
        with pytest.raises(KeyError):
            store.restore(doc_id)


def test_a_purged_id_can_be_reused_for_a_fresh_document(store):
    store.trash("notes")
    store.purge_trash()
    store.add_document("notes", "Fresh notes", "Start again.")
    assert store.get_title("notes") == "Fresh notes"
    assert store.get_tags("notes") == []
    assert store.get_documents() == ["todo", "post", "notes"]
    assert store.get_documents("work") == ["post"]


def test_trashed_is_reported_before_a_bad_body_or_tag(store):
    store.trash("notes")
    with pytest.raises(DocumentTrashed):
        store.update_body("notes", None)
    with pytest.raises(DocumentTrashed):
        store.tag_document("notes", "")
    with pytest.raises(KeyError):
        store.update_body("missing", None)


def test_document_trashed_is_a_store_error():
    assert issubclass(DocumentTrashed, StoreError)
