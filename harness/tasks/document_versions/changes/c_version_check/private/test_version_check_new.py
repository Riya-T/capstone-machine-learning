"""Hidden tests for the c_version_check change (page versions and conflict
detection). Never shown to the writer or the editor.

Usage (with wiki.py importable, e.g. in the sandbox):
    python -m pytest changes/c_version_check/private/test_version_check_new.py
"""

import pytest
from wiki import VersionConflict, Wiki, WikiError


@pytest.fixture
def wiki():
    w = Wiki()
    w.create_page("home", "ann", "v1")
    w.create_page("faq", "bob", "q1")
    return w


def state(w):
    return {
        p: (w.get_text(p), w.get_revision_count(p), w.get_authors(p), w.get_version(p))
        for p in w.get_pages()
    }


def test_version_new_pages_start_at_one(wiki):
    assert wiki.get_version("home") == 1
    assert wiki.get_version("faq") == 1


def test_version_goes_up_per_page(wiki):
    wiki.edit_page("home", "bob", "v2")
    wiki.edit_page("home", "bob", "v3")
    wiki.edit_page("faq", "ann", "q2")
    assert wiki.get_version("home") == 3
    assert wiki.get_version("faq") == 2


def test_version_matching_expected_version_is_accepted(wiki):
    wiki.edit_page("home", "bob", "v2", expected_version=1)
    wiki.edit_page("home", "cy", "v3", expected_version=2)
    assert wiki.get_text("home") == "v3"
    assert wiki.get_version("home") == 3
    assert wiki.get_authors("home") == ["ann", "bob", "cy"]


@pytest.mark.parametrize("expected", [0, 2, 5])
def test_version_mismatch_changes_nothing(wiki, expected):
    before = state(wiki)
    with pytest.raises(VersionConflict):
        wiki.edit_page("home", "bob", "v2", expected_version=expected)
    assert state(wiki) == before


def test_version_none_means_no_check(wiki):
    wiki.edit_page("home", "bob", "v2")
    wiki.edit_page("home", "bob", "v3", expected_version=None)
    assert wiki.get_version("home") == 3


def test_version_failed_edits_do_not_count(wiki):
    for bad in (
        lambda: wiki.edit_page("home", "bob", "v1"),
        lambda: wiki.edit_page("home", "", "x"),
        lambda: wiki.edit_page("home", "bob", "x", expected_version=9),
    ):
        with pytest.raises((ValueError, WikiError)):
            bad()
    assert wiki.get_version("home") == 1


def test_version_conflict_is_a_wiki_error():
    assert issubclass(VersionConflict, WikiError)


def test_version_of_missing_page_raises_key_error(wiki):
    with pytest.raises(KeyError):
        wiki.get_version("about")
    with pytest.raises(KeyError):
        wiki.get_version(None)


def test_version_missing_page_is_reported_before_a_conflict(wiki):
    with pytest.raises(KeyError):
        wiki.edit_page("about", "bob", "x", expected_version=7)


def test_version_bad_arguments_are_reported_before_a_conflict(wiki):
    with pytest.raises(ValueError):
        wiki.edit_page("home", "", "x", expected_version=7)
    with pytest.raises(ValueError):
        wiki.edit_page("home", "bob", None, expected_version=7)


def test_version_conflict_is_reported_before_an_unchanged_text(wiki):
    with pytest.raises(VersionConflict):
        wiki.edit_page("home", "bob", "v1", expected_version=4)


def test_version_keeps_counting_after_old_revisions_are_dropped(wiki):
    for n in range(2, 9):
        wiki.edit_page("home", "bob", f"v{n}", expected_version=n - 1)
    assert wiki.get_version("home") == 8
    with pytest.raises(IndexError):
        wiki.get_revision("home", 3)
