"""Hidden tests for the c_search change (finding pages and contributions).
Never shown to the writer or the editor.

Usage (with wiki.py importable, e.g. in the sandbox):
    python -m pytest changes/c_search/private/test_search_new.py
"""

import pytest
from wiki import Wiki, WikiError


@pytest.fixture
def wiki():
    w = Wiki()
    w.create_page("zoo", "ann", "Lions and tigers")
    w.create_page("farm", "bob", "Cows and pigs")
    w.create_page("pond", "ann", "Ducks")
    return w


def test_search_results_follow_creation_order(wiki):
    assert wiki.find_pages("and") == ["zoo", "farm"]
    assert wiki.find_pages("s") == ["zoo", "farm", "pond"]


def test_search_is_case_sensitive(wiki):
    assert wiki.find_pages("lions") == []
    assert wiki.find_pages("Lions") == ["zoo"]


def test_search_looks_only_at_current_text(wiki):
    wiki.edit_page("zoo", "bob", "Bears")
    assert wiki.find_pages("Lions") == []
    assert wiki.find_pages("Bears") == ["zoo"]


def test_search_matches_whole_text_and_inner_parts(wiki):
    assert wiki.find_pages("Ducks") == ["pond"]
    assert wiki.find_pages("ows and p") == ["farm"]


def test_search_ignores_empty_pages():
    w = Wiki()
    w.create_page("blank", "ann", "")
    w.create_page("full", "ann", "x")
    assert w.find_pages("x") == ["full"]


@pytest.mark.parametrize("phrase", ["", None, 3])
def test_search_invalid_phrases_raise_value_error(wiki, phrase):
    with pytest.raises(ValueError):
        wiki.find_pages(phrase)


def test_search_contributions_are_in_writing_order(wiki):
    wiki.edit_page("farm", "ann", "Sheep")
    wiki.edit_page("zoo", "ann", "Bears")
    wiki.edit_page("farm", "ann", "Goats")
    assert wiki.get_contributions("ann") == [
        ("zoo", 1),
        ("pond", 1),
        ("farm", 2),
        ("zoo", 2),
        ("farm", 3),
    ]
    assert wiki.get_contributions("bob") == [("farm", 1)]


def test_search_contributions_include_dropped_revisions():
    w = Wiki()
    w.create_page("home", "ann", "r1")
    for n in range(2, 9):
        w.edit_page("home", "bob" if n % 2 else "cy", f"r{n}")
    with pytest.raises(IndexError):
        w.get_revision("home", 1)
    assert w.get_contributions("ann") == [("home", 1)]
    assert w.get_contributions("bob") == [("home", 3), ("home", 5), ("home", 7)]
    assert w.get_contributions("cy") == [("home", 2), ("home", 4), ("home", 6), ("home", 8)]


def test_search_failed_edits_are_not_contributions(wiki):
    with pytest.raises(WikiError):
        wiki.edit_page("pond", "cy", "Ducks")
    with pytest.raises(ValueError):
        wiki.edit_page("pond", "cy", None)
    assert wiki.get_contributions("cy") == []


def test_search_does_not_change_anything(wiki):
    wiki.find_pages("and")
    wiki.get_contributions("ann")
    assert wiki.get_pages() == ["zoo", "farm", "pond"]
    assert wiki.get_revision_count("zoo") == 1
