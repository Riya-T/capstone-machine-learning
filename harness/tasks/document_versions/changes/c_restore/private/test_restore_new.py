"""Hidden tests for the c_restore change (restoring an earlier revision).
Never shown to the writer or the editor.

Usage (with wiki.py importable, e.g. in the sandbox):
    python -m pytest changes/c_restore/private/test_restore_new.py
"""

import pytest
from wiki import VersionConflict, Wiki, WikiError


@pytest.fixture
def wiki():
    """home has revisions r1..r4 by ann, bob, cy, bob; faq has one."""
    w = Wiki()
    w.create_page("home", "ann", "r1")
    w.edit_page("home", "bob", "r2")
    w.edit_page("home", "cy", "r3")
    w.edit_page("home", "bob", "r4")
    w.create_page("faq", "dee", "q1")
    return w


def readable(w, page):
    found = []
    for number in range(1, w.get_revision_count(page) + 1):
        try:
            w.get_revision(page, number)
        except IndexError:
            continue
        found.append(number)
    return found


def state(w):
    return {
        p: (
            w.get_text(p),
            w.get_revision_count(p),
            [w.get_revision(p, n) for n in readable(w, p)],
            w.get_authors(p),
            w.get_version(p),
        )
        for p in w.get_pages()
    }


def test_restore_to_a_middle_revision(wiki):
    wiki.restore("home", 2)
    assert wiki.get_text("home") == "r2"
    assert wiki.get_revision_count("home") == 2
    assert readable(wiki, "home") == [1, 2]
    for gone in (3, 4):
        with pytest.raises(IndexError):
            wiki.get_revision("home", gone)


def test_restore_drops_authors_of_discarded_revisions_only(wiki):
    wiki.restore("home", 2)
    assert wiki.get_authors("home") == ["ann", "bob"]
    wiki.restore("home", 1)
    assert wiki.get_authors("home") == ["ann"]


def test_restore_new_edits_take_the_freed_numbers(wiki):
    wiki.restore("home", 2)
    wiki.edit_page("home", "eve", "n3")
    wiki.edit_page("home", "eve", "n4")
    assert [wiki.get_revision("home", n) for n in (1, 2, 3, 4)] == ["r1", "r2", "n3", "n4"]
    assert wiki.get_authors("home") == ["ann", "bob", "eve"]


def test_restore_counts_as_a_change_and_versions_never_go_down(wiki):
    assert wiki.get_version("home") == 4
    wiki.restore("home", 1)
    assert wiki.get_version("home") == 5
    wiki.edit_page("home", "bob", "x")
    assert wiki.get_version("home") == 6
    assert wiki.get_version("faq") == 1


def test_restore_with_the_right_expected_version(wiki):
    wiki.restore("home", 3, expected_version=4)
    assert wiki.get_text("home") == "r3"
    assert wiki.get_version("home") == 5


def test_restore_with_a_stale_version_changes_nothing(wiki):
    before = state(wiki)
    with pytest.raises(VersionConflict):
        wiki.restore("home", 1, expected_version=3)
    assert state(wiki) == before


def test_restore_never_revives_revisions_that_were_dropped():
    w = Wiki(keep=3)
    w.create_page("home", "ann", "r1")
    for n in range(2, 7):
        w.edit_page("home", "bob", f"r{n}")
    assert readable(w, "home") == [4, 5, 6]
    w.restore("home", 5)
    assert readable(w, "home") == [4, 5]
    with pytest.raises(IndexError):
        w.get_revision("home", 3)
    w.edit_page("home", "cy", "n6")
    assert readable(w, "home") == [4, 5, 6]
    w.edit_page("home", "cy", "n7")
    assert readable(w, "home") == [5, 6, 7]
    assert w.get_authors("home") == ["ann", "bob", "cy"]


def test_restore_to_a_revision_no_longer_kept_raises_index_error():
    w = Wiki(keep=2)
    w.create_page("home", "ann", "r1")
    for n in range(2, 5):
        w.edit_page("home", "bob", f"r{n}")
    before = state(w)
    with pytest.raises(IndexError):
        w.restore("home", 2)
    assert state(w) == before


def test_restore_to_a_revision_past_the_latest_raises_index_error(wiki):
    before = state(wiki)
    with pytest.raises(IndexError):
        wiki.restore("home", 5)
    assert state(wiki) == before


def test_restore_to_the_latest_revision_is_refused(wiki):
    before = state(wiki)
    with pytest.raises(WikiError):
        wiki.restore("home", 4)
    with pytest.raises(WikiError):
        wiki.restore("faq", 1)
    assert state(wiki) == before


@pytest.mark.parametrize("number", [0, -1, 2.0, "2", None])
def test_restore_invalid_numbers_raise_value_error(wiki, number):
    before = state(wiki)
    with pytest.raises(ValueError):
        wiki.restore("home", number)
    assert state(wiki) == before


def test_restore_error_precedence(wiki):
    with pytest.raises(KeyError):
        wiki.restore("about", 0, expected_version=9)
    with pytest.raises(ValueError):
        wiki.restore("home", 0, expected_version=9)
    with pytest.raises(VersionConflict):
        wiki.restore("home", 9, expected_version=9)
    with pytest.raises(VersionConflict):
        wiki.restore("home", 4, expected_version=9)
    with pytest.raises(IndexError):
        wiki.restore("home", 9, expected_version=4)
