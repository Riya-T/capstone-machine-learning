"""Hidden tests for the initial document_versions spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with wiki.py importable, e.g. in the sandbox):
    python -m pytest private/test_wiki_initial.py
"""

import pytest
from wiki import Wiki, WikiError


@pytest.fixture
def wiki():
    w = Wiki()
    w.create_page("home", "ann", "v1")
    w.create_page("faq", "bob", "")
    return w


def numbers(w, page):
    """The revision numbers in a page's history."""
    return [number for number, _ in w.get_history(page)]


def state(w):
    """Every page's text, revisions and authors, to check that a failed call
    changed nothing."""
    return {
        p: (
            w.get_text(p),
            w.get_revision_count(p),
            list(w.get_history(p)),
            sorted(w.get_authors(p)),
        )
        for p in w.get_pages()
    }


# --- pages ------------------------------------------------------------------


def test_pages_are_listed_in_creation_order():
    w = Wiki()
    for name in ["zeta", "alpha", "mid"]:
        w.create_page(name, "ann", "x")
    assert w.get_pages() == ["zeta", "alpha", "mid"]


def test_a_page_may_start_empty(wiki):
    assert wiki.get_text("faq") == ""
    assert wiki.get_history("faq") == [(1, "")]
    assert wiki.get_authors("faq") == ["bob"]


@pytest.mark.parametrize(
    "args",
    [
        ("", "ann", "x"),
        (None, "ann", "x"),
        ("p", "", "x"),
        ("p", None, "x"),
        ("p", "ann", None),
        ("p", "ann", 3),
    ],
)
def test_invalid_create_arguments_are_rejected(args):
    w = Wiki()
    with pytest.raises(ValueError):
        w.create_page(*args)
    assert w.get_pages() == []


def test_creating_an_existing_page_is_rejected(wiki):
    wiki.edit_page("home", "bob", "v2")
    before = state(wiki)
    with pytest.raises(WikiError):
        wiki.create_page("home", "cy", "fresh")
    assert state(wiki) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda w: w.edit_page("about", "ann", "x"),
        lambda w: w.get_text("about"),
        lambda w: w.get_history("about"),
        lambda w: w.get_revision_count("about"),
        lambda w: w.get_authors("about"),
        lambda w: w.get_text(None),
        lambda w: w.get_history(1),
    ],
)
def test_pages_that_do_not_exist_raise_key_error(wiki, call):
    before = state(wiki)
    with pytest.raises(KeyError):
        call(wiki)
    assert state(wiki) == before


# --- revisions --------------------------------------------------------------


def test_every_revision_is_in_the_history(wiki):
    wiki.edit_page("home", "bob", "v2")
    wiki.edit_page("home", "ann", "v3")
    assert wiki.get_history("home") == [(1, "v1"), (2, "v2"), (3, "v3")]
    assert wiki.get_text("home") == "v3"
    assert wiki.get_revision_count("home") == 3


def test_pages_keep_separate_revisions(wiki):
    wiki.edit_page("home", "bob", "v2")
    wiki.edit_page("faq", "cy", "Q?")
    assert wiki.get_revision_count("home") == 2
    assert wiki.get_revision_count("faq") == 2
    assert wiki.get_history("faq") == [(1, ""), (2, "Q?")]
    assert sorted(wiki.get_authors("faq")) == ["bob", "cy"]


def test_an_old_text_may_be_written_again(wiki):
    wiki.edit_page("home", "bob", "v2")
    wiki.edit_page("home", "bob", "v1")
    assert wiki.get_revision_count("home") == 3
    assert wiki.get_text("home") == "v1"
    assert wiki.get_history("home") == [(1, "v1"), (2, "v2"), (3, "v1")]


def test_an_unchanged_edit_adds_nothing(wiki):
    wiki.edit_page("home", "bob", "v2")
    before = state(wiki)
    with pytest.raises(WikiError):
        wiki.edit_page("home", "cy", "v2")
    assert state(wiki) == before
    assert "cy" not in wiki.get_authors("home")


@pytest.mark.parametrize("author,text", [("", "x"), (None, "x"), ("bob", None), ("bob", 5)])
def test_invalid_edits_are_rejected(wiki, author, text):
    before = state(wiki)
    with pytest.raises(ValueError):
        wiki.edit_page("home", author, text)
    assert state(wiki) == before


# --- the history: the 5 latest revisions -------------------------------------


def test_five_revisions_are_all_kept(wiki):
    for n in range(2, 6):
        wiki.edit_page("home", "bob", f"v{n}")
    assert numbers(wiki, "home") == [1, 2, 3, 4, 5]
    assert wiki.get_history("home")[0] == (1, "v1")


def test_a_sixth_revision_leaves_out_the_first():
    w = Wiki()
    w.create_page("home", "ann", "a")
    for text in "bcdef":
        w.edit_page("home", "bob", text)
    assert w.get_history("home") == [(2, "b"), (3, "c"), (4, "d"), (5, "e"), (6, "f")]


def test_only_the_five_latest_revisions_are_kept(wiki):
    for n in range(2, 9):
        wiki.edit_page("home", "bob", f"v{n}")
    assert wiki.get_revision_count("home") == 8
    assert wiki.get_history("home") == [(4, "v4"), (5, "v5"), (6, "v6"), (7, "v7"), (8, "v8")]
    for n in range(9, 13):
        wiki.edit_page("home", "bob", f"v{n}")
    assert numbers(wiki, "home") == [8, 9, 10, 11, 12]
    assert wiki.get_revision_count("home") == 12


def test_the_history_ends_with_the_current_text(wiki):
    for n in range(2, 10):
        wiki.edit_page("home", "bob", f"v{n}")
        assert wiki.get_history("home")[-1] == (n, f"v{n}")
        assert wiki.get_text("home") == f"v{n}"


def test_the_history_is_per_page(wiki):
    for n in range(2, 8):
        wiki.edit_page("home", "bob", f"v{n}")
    wiki.edit_page("faq", "bob", "Q")
    assert numbers(wiki, "home") == [3, 4, 5, 6, 7]
    assert wiki.get_history("faq") == [(1, ""), (2, "Q")]


def test_authors_of_older_revisions_still_count(wiki):
    wiki.edit_page("home", "cy", "v2")
    for n in range(3, 10):
        wiki.edit_page("home", "bob", f"v{n}")
    assert numbers(wiki, "home") == [5, 6, 7, 8, 9]
    assert sorted(wiki.get_authors("home")) == ["ann", "bob", "cy"]


def test_an_unchanged_edit_is_checked_against_the_current_text_only(wiki):
    for n in range(2, 8):
        wiki.edit_page("home", "bob", f"v{n}")
    wiki.edit_page("home", "bob", "v1")
    assert wiki.get_history("home")[-1] == (8, "v1")
    with pytest.raises(WikiError):
        wiki.edit_page("home", "bob", "v1")
    assert wiki.get_revision_count("home") == 8


def test_each_author_is_listed_once(wiki):
    # The order of get_authors is unspecified.
    wiki.edit_page("faq", "dee", "a")
    wiki.edit_page("faq", "bob", "b")
    wiki.edit_page("faq", "ann", "c")
    wiki.edit_page("faq", "dee", "d")
    assert sorted(wiki.get_authors("faq")) == ["ann", "bob", "dee"]


def test_wikis_do_not_share_pages():
    first, second = Wiki(), Wiki()
    first.create_page("home", "ann", "x")
    assert second.get_pages() == []
    second.create_page("home", "bob", "y")
    assert first.get_text("home") == "x"
