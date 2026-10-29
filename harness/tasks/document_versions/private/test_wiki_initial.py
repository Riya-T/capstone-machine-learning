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


def readable(w, page):
    """Every revision number of a page that get_revision can still read."""
    found = []
    for number in range(1, w.get_revision_count(page) + 1):
        try:
            w.get_revision(page, number)
        except IndexError:
            continue
        found.append(number)
    return found


def state(w):
    """Every page's text, revisions and authors, to check that a failed call
    changed nothing."""
    return {
        p: (
            w.get_text(p),
            w.get_revision_count(p),
            [w.get_revision(p, n) for n in readable(w, p)],
            w.get_authors(p),
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
    assert wiki.get_revision("faq", 1) == ""
    assert wiki.get_authors("faq") == ["bob"]


@pytest.mark.parametrize(
    "args",
    [
        ("", "ann", "x"),
        (None, "ann", "x"),
        ("p", "", "x"),
        ("p", 7, "x"),
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


def test_a_bad_argument_is_reported_before_a_duplicate_page(wiki):
    with pytest.raises(ValueError):
        wiki.create_page("home", "", "x")


@pytest.mark.parametrize(
    "call",
    [
        lambda w: w.edit_page("about", "ann", "x"),
        lambda w: w.get_text("about"),
        lambda w: w.get_revision("about", 1),
        lambda w: w.get_revision_count("about"),
        lambda w: w.get_authors("about"),
        lambda w: w.get_text(None),
        lambda w: w.get_text(1),
    ],
)
def test_pages_that_do_not_exist_raise_key_error(wiki, call):
    before = state(wiki)
    with pytest.raises(KeyError):
        call(wiki)
    assert state(wiki) == before


# --- revisions --------------------------------------------------------------


def test_every_revision_can_be_read_back(wiki):
    wiki.edit_page("home", "bob", "v2")
    wiki.edit_page("home", "ann", "v3")
    assert [wiki.get_revision("home", n) for n in (1, 2, 3)] == ["v1", "v2", "v3"]
    assert wiki.get_text("home") == "v3"
    assert wiki.get_revision_count("home") == 3


def test_pages_keep_separate_revisions(wiki):
    wiki.edit_page("home", "bob", "v2")
    wiki.edit_page("faq", "cy", "Q?")
    assert wiki.get_revision_count("home") == 2
    assert wiki.get_revision_count("faq") == 2
    assert wiki.get_revision("faq", 2) == "Q?"
    assert wiki.get_authors("faq") == ["bob", "cy"]


def test_an_old_text_may_be_written_again(wiki):
    wiki.edit_page("home", "bob", "v2")
    wiki.edit_page("home", "bob", "v1")
    assert wiki.get_revision_count("home") == 3
    assert wiki.get_text("home") == "v1"


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


def test_a_bad_edit_is_reported_before_an_unchanged_text(wiki):
    with pytest.raises(ValueError):
        wiki.edit_page("home", "", "v1")


@pytest.mark.parametrize("number", [0, -1, 1.0, "1", None])
def test_invalid_revision_numbers_raise_value_error(wiki, number):
    with pytest.raises(ValueError):
        wiki.get_revision("home", number)


def test_revisions_past_the_latest_raise_index_error(wiki):
    wiki.edit_page("home", "bob", "v2")
    with pytest.raises(IndexError):
        wiki.get_revision("home", 3)
    with pytest.raises(IndexError):
        wiki.get_revision("home", 100)


# --- keeping only recent revisions ------------------------------------------


def test_five_revisions_are_all_kept(wiki):
    for n in range(2, 6):
        wiki.edit_page("home", "bob", f"v{n}")
    assert readable(wiki, "home") == [1, 2, 3, 4, 5]
    assert wiki.get_revision("home", 1) == "v1"


def test_only_the_five_most_recent_revisions_are_kept(wiki):
    for n in range(2, 9):
        wiki.edit_page("home", "bob", f"v{n}")
    assert wiki.get_revision_count("home") == 8
    assert readable(wiki, "home") == [4, 5, 6, 7, 8]
    assert [wiki.get_revision("home", n) for n in (4, 8)] == ["v4", "v8"]
    for old in (1, 2, 3):
        with pytest.raises(IndexError):
            wiki.get_revision("home", old)


def test_dropping_old_revisions_is_per_page(wiki):
    for n in range(2, 8):
        wiki.edit_page("home", "bob", f"v{n}")
    wiki.edit_page("faq", "bob", "Q")
    assert readable(wiki, "faq") == [1, 2]
    assert wiki.get_revision("faq", 1) == ""


def test_authors_of_dropped_revisions_still_count(wiki):
    wiki.edit_page("home", "cy", "v2")
    for n in range(3, 10):
        wiki.edit_page("home", "bob", f"v{n}")
    assert readable(wiki, "home") == [5, 6, 7, 8, 9]
    assert wiki.get_authors("home") == ["ann", "cy", "bob"]


def test_authors_are_in_order_of_their_first_revision(wiki):
    wiki.edit_page("faq", "dee", "a")
    wiki.edit_page("faq", "bob", "b")
    wiki.edit_page("faq", "ann", "c")
    wiki.edit_page("faq", "dee", "d")
    assert wiki.get_authors("faq") == ["bob", "dee", "ann"]


def test_wikis_do_not_share_pages():
    first, second = Wiki(), Wiki()
    first.create_page("home", "ann", "x")
    assert second.get_pages() == []
    second.create_page("home", "bob", "y")
    assert first.get_text("home") == "x"
