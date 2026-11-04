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
    assert wiki.get_history("home") == [(1, "Welcome")]


def test_edits_add_numbered_revisions(wiki):
    wiki.edit_page("home", "bob", "Welcome!")
    wiki.edit_page("home", "ann", "Welcome, all")
    assert wiki.get_text("home") == "Welcome, all"
    assert wiki.get_revision_count("home") == 3
    assert wiki.get_history("home") == [(1, "Welcome"), (2, "Welcome!"), (3, "Welcome, all")]


def test_authors_are_listed_once_each(wiki):
    wiki.edit_page("home", "zoe", "Hi")
    wiki.edit_page("home", "bob", "Hello")
    wiki.edit_page("home", "ann", "Hello again")
    assert sorted(wiki.get_authors("home")) == ["ann", "bob", "zoe"]  # in any order


def test_an_edit_that_changes_nothing_is_refused(wiki):
    with pytest.raises(WikiError):
        wiki.edit_page("home", "bob", "Welcome")
    assert wiki.get_revision_count("home") == 1


def test_unknown_page_raises_key_error(wiki):
    with pytest.raises(KeyError):
        wiki.get_text("about")


def test_the_history_keeps_the_5_latest_revisions():
    w = Wiki()
    w.create_page("home", "ann", "v1")
    for n in range(2, 6):
        w.edit_page("home", "bob", f"v{n}")
    assert w.get_history("home") == [(1, "v1"), (2, "v2"), (3, "v3"), (4, "v4"), (5, "v5")]
    w.edit_page("home", "bob", "v6")
    assert w.get_history("home") == [(2, "v2"), (3, "v3"), (4, "v4"), (5, "v5"), (6, "v6")]
    w.edit_page("home", "bob", "v7")
    w.edit_page("home", "bob", "v8")
    assert w.get_history("home") == [(4, "v4"), (5, "v5"), (6, "v6"), (7, "v7"), (8, "v8")]
    assert w.get_revision_count("home") == 8
    assert w.get_text("home") == "v8"
