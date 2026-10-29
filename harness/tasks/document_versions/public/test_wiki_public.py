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
    wiki.edit_page("home", "zoe", "Hi")
    wiki.edit_page("home", "bob", "Hello")
    wiki.edit_page("home", "ann", "Hello again")
    assert wiki.get_authors("home") == ["ann", "zoe", "bob"]  # order of first revision


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


def test_old_revisions_are_dropped_but_keep_their_numbers(wiki):
    for n in range(2, 9):
        wiki.edit_page("home", "bob", f"v{n}")
    assert wiki.get_revision_count("home") == 8
    assert wiki.get_text("home") == "v8"
    assert wiki.get_revision("home", 8) == "v8"
    assert wiki.get_revision("home", 4) == "v4"
    with pytest.raises(IndexError):
        wiki.get_revision("home", 1)
