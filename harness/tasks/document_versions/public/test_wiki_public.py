"""Public checks for wiki.py.

Usage (with wiki.py importable, e.g. in the sandbox):
    python -m pytest public/test_wiki_public.py
"""

import pytest
from wiki import Wiki, WikiError


@pytest.fixture
def wiki():
    w = Wiki()
    w.create_page("home", "ann", "Welcome")
    return w


def test_a_new_page_has_one_revision(wiki):
    assert wiki.get_text("home") == "Welcome"
    assert wiki.get_revision_count("home") == 1
    assert wiki.get_revision("home", 1) == "Welcome"


def test_edits_add_numbered_revisions(wiki):
    wiki.edit_page("home", "bob", "Welcome!")
    wiki.edit_page("home", "ann", "Welcome, all")
    assert wiki.get_text("home") == "Welcome, all"
    assert wiki.get_revision_count("home") == 3
    assert wiki.get_revision("home", 2) == "Welcome!"


def test_authors_are_listed_once_each(wiki):
    wiki.edit_page("home", "bob", "Hi")
    wiki.edit_page("home", "ann", "Hello")
    assert wiki.get_authors("home") == ["ann", "bob"]


def test_an_edit_that_changes_nothing_is_refused(wiki):
    with pytest.raises(WikiError):
        wiki.edit_page("home", "bob", "Welcome")
    assert wiki.get_revision_count("home") == 1


def test_a_revision_that_does_not_exist_yet_raises_index_error(wiki):
    with pytest.raises(IndexError):
        wiki.get_revision("home", 2)


def test_unknown_page_raises_key_error(wiki):
    with pytest.raises(KeyError):
        wiki.get_text("about")
