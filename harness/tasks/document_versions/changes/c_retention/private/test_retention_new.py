"""Hidden tests for the c_retention change (adjustable number of kept
revisions). Never shown to the writer or the editor.

Usage (with wiki.py importable, e.g. in the sandbox):
    python -m pytest changes/c_retention/private/test_retention_new.py
"""

import pytest
from wiki import Wiki, WikiError

BAD_KEEPS = [0, -2, 2.0, "3", True]


def readable(w, page):
    found = []
    for number in range(1, w.get_revision_count(page) + 1):
        try:
            w.get_revision(page, number)
        except IndexError:
            continue
        found.append(number)
    return found


def write(w, page, count):
    """Make `count` more revisions of a page, with texts r2, r3, ..."""
    start = w.get_revision_count(page) + 1
    for n in range(start, start + count):
        w.edit_page(page, "bob", f"r{n}")


def test_retention_default_is_still_five():
    w = Wiki()
    w.create_page("home", "ann", "r1")
    write(w, "home", 6)
    assert w.get_keep("home") == 5
    assert readable(w, "home") == [3, 4, 5, 6, 7]


def test_retention_wiki_limit_applies_to_every_page():
    w = Wiki(keep=3)
    w.create_page("home", "ann", "r1")
    w.create_page("faq", "ann", "r1")
    write(w, "home", 4)
    write(w, "faq", 1)
    assert readable(w, "home") == [3, 4, 5]
    assert readable(w, "faq") == [1, 2]
    assert w.get_keep("faq") == 3


def test_retention_a_limit_of_one_keeps_only_the_latest():
    w = Wiki(keep=1)
    w.create_page("home", "ann", "r1")
    write(w, "home", 2)
    assert readable(w, "home") == [3]
    assert w.get_text("home") == "r3"
    assert w.get_revision_count("home") == 3


def test_retention_page_limits_are_independent():
    w = Wiki(keep=2)
    w.create_page("long", "ann", "r1", keep=6)
    w.create_page("short", "ann", "r1", keep=None)
    w.create_page("tiny", "ann", "r1", keep=1)
    for page in ("long", "short", "tiny"):
        write(w, page, 6)
    assert readable(w, "long") == [2, 3, 4, 5, 6, 7]
    assert readable(w, "short") == [6, 7]
    assert readable(w, "tiny") == [7]
    assert [w.get_keep(p) for p in ("long", "short", "tiny")] == [6, 2, 1]


def test_retention_dropped_revisions_still_count_elsewhere():
    w = Wiki(keep=2)
    w.create_page("home", "ann", "r1")
    w.edit_page("home", "cy", "r2")
    write(w, "home", 3)
    assert readable(w, "home") == [4, 5]
    assert w.get_revision_count("home") == 5
    assert w.get_authors("home") == ["ann", "cy", "bob"]


@pytest.mark.parametrize("keep", BAD_KEEPS)
def test_retention_invalid_wiki_limits_are_rejected(keep):
    with pytest.raises(ValueError):
        Wiki(keep=keep)


@pytest.mark.parametrize("keep", BAD_KEEPS)
def test_retention_invalid_page_limits_create_nothing(keep):
    w = Wiki()
    with pytest.raises(ValueError):
        w.create_page("home", "ann", "x", keep=keep)
    assert w.get_pages() == []


def test_retention_bad_limit_is_reported_before_a_duplicate_page():
    w = Wiki()
    w.create_page("home", "ann", "x", keep=4)
    with pytest.raises(ValueError):
        w.create_page("home", "bob", "y", keep=0)
    with pytest.raises(WikiError):
        w.create_page("home", "bob", "y", keep=2)
    assert w.get_keep("home") == 4
    assert w.get_text("home") == "x"


def test_retention_limit_of_missing_page_raises_key_error():
    w = Wiki()
    with pytest.raises(KeyError):
        w.get_keep("home")
    with pytest.raises(KeyError):
        w.get_keep(None)


def test_retention_wikis_do_not_share_limits():
    big, small = Wiki(keep=9), Wiki(keep=1)
    big.create_page("home", "ann", "r1")
    small.create_page("home", "ann", "r1")
    write(big, "home", 3)
    write(small, "home", 3)
    assert readable(big, "home") == [1, 2, 3, 4]
    assert readable(small, "home") == [4]
