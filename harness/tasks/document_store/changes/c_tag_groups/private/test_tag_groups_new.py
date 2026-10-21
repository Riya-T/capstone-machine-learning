"""Hidden tests for the c_tag_groups change (tag groups). Never shown to the
writer or the editor.

Usage (with docstore.py importable, e.g. in the sandbox):
    python -m pytest changes/c_tag_groups/private/test_tag_groups_new.py
"""

import pytest
from docstore import DocumentStore, StoreError


@pytest.fixture
def store():
    st = DocumentStore()
    st.add_document("notes", "Meeting notes", "Ship on Monday.")
    st.add_document("todo", "Things to do", "Buy milk.")
    st.add_document("post", "Blog post", "Hello world.")
    st.tag_document("notes", "final")
    st.tag_document("post", "draft")
    st.tag_document("post", "review")
    st.create_group("status")
    st.create_group("place")
    st.add_tag_to_group("status", "draft")
    st.add_tag_to_group("status", "review")
    st.add_tag_to_group("status", "final")
    return st


def groups(st):
    return {g: st.get_group_tags(g) for g in st.get_groups()}


def test_group_tags_are_listed_in_the_order_added(store):
    assert store.get_group_tags("status") == ["draft", "review", "final"]
    assert store.get_group_tags("place") == []
    store.create_group("audience")
    assert store.get_groups() == ["status", "place", "audience"]


def test_documents_in_a_group_are_in_add_order_each_once(store):
    # "post" carries two tags of the group but is listed once.
    assert store.get_documents_in_group("status") == ["notes", "post"]
    assert store.get_documents_in_group("place") == []


def test_tags_added_to_a_group_later_count(store):
    store.tag_document("todo", "home")
    store.tag_document("notes", "office")
    assert store.get_documents_in_group("place") == []
    store.add_tag_to_group("place", "office")
    assert store.get_documents_in_group("place") == ["notes"]
    store.add_tag_to_group("place", "home")
    assert store.get_documents_in_group("place") == ["notes", "todo"]


def test_documents_tagged_later_count(store):
    store.add_tag_to_group("place", "home")
    store.tag_document("todo", "home")
    store.add_document("memo", "Memo", "")
    store.tag_document("memo", "home")
    assert store.get_documents_in_group("place") == ["todo", "memo"]


def test_a_tag_belongs_to_at_most_one_group(store):
    before = groups(store)
    with pytest.raises(StoreError):
        store.add_tag_to_group("place", "draft")
    assert groups(store) == before
    assert store.get_documents_in_group("place") == []
    store.add_tag_to_group("status", "draft")  # its own group again is harmless
    assert groups(store) == before


def test_a_tag_may_join_a_group_before_any_document_has_it(store):
    store.add_tag_to_group("place", "beach")
    assert store.get_group_tags("place") == ["beach"]
    assert store.get_documents_in_group("place") == []
    store.tag_document("notes", "beach")
    assert store.get_documents_in_group("place") == ["notes"]


@pytest.mark.parametrize("bad_name", ["", None, 4])
def test_invalid_group_names_are_rejected(store, bad_name):
    with pytest.raises(ValueError):
        store.create_group(bad_name)
    assert store.get_groups() == ["status", "place"]


def test_creating_a_group_twice_is_rejected(store):
    with pytest.raises(StoreError):
        store.create_group("status")
    assert store.get_group_tags("status") == ["draft", "review", "final"]
    assert store.get_groups() == ["status", "place"]


@pytest.mark.parametrize("bad_tag", ["", None, 4])
def test_invalid_tags_cannot_join_a_group(store, bad_tag):
    with pytest.raises(ValueError):
        store.add_tag_to_group("place", bad_tag)
    assert store.get_group_tags("place") == []


@pytest.mark.parametrize(
    "call",
    [
        lambda st: st.add_tag_to_group("topic", "home"),
        lambda st: st.get_group_tags("topic"),
        lambda st: st.get_documents_in_group("topic"),
        lambda st: st.get_group_tags(None),
    ],
)
def test_groups_that_do_not_exist_raise_key_error(store, call):
    before = groups(store)
    with pytest.raises(KeyError):
        call(store)
    assert groups(store) == before


def test_group_errors_come_in_the_stated_order(store):
    with pytest.raises(KeyError):
        store.add_tag_to_group("topic", "")  # missing group before bad tag
    with pytest.raises(ValueError):
        store.add_tag_to_group("place", "")  # bad tag before anything else


def test_groups_leave_plain_tag_listing_alone(store):
    assert store.get_documents("draft") == ["post"]
    assert store.get_tags("post") == ["draft", "review"]
    assert store.get_documents() == ["notes", "todo", "post"]
