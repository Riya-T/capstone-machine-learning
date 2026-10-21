"""Hidden tests for the c_alias change (code rules). Never shown to the
writer or the editor.

Usage (with shortener.py importable, e.g. in the sandbox):
    python -m pytest changes/c_alias/private/test_alias_new.py
"""

import pytest
from shortener import ReservedCode, Shortener, ShortenerError

SALE = "https://example.com/sale"
DOCS = "https://example.com/docs"
BAD_CODES = ["spring sale", "sale!", "café", "a/b", "a" * 33, "", None, 7]
GOOD_CODES = ["a", "A-1", "under_score", "MiXeD", "a" * 32, "0123456789"]


@pytest.fixture
def links():
    sh = Shortener(reserved=("admin", "Login"))
    sh.add_link("Promo", SALE)
    sh.add_link("docs", DOCS)
    return sh


def state(sh):
    return {c: (sh.get_target(c), sh.get_hits(c)) for c in sh.get_codes()}


@pytest.mark.parametrize("code", BAD_CODES)
def test_codes_outside_the_rules_are_rejected(links, code):
    before = state(links)
    with pytest.raises(ValueError):
        links.add_link(code, SALE)
    assert state(links) == before


@pytest.mark.parametrize("code", GOOD_CODES)
def test_codes_within_the_rules_are_accepted(code):
    sh = Shortener()
    sh.add_link(code, SALE)
    assert sh.get_codes() == [code]


@pytest.mark.parametrize("spelling", ["promo", "PROMO", "pRoMo"])
def test_adding_the_same_code_in_another_case_is_a_duplicate(links, spelling):
    before = state(links)
    with pytest.raises(ShortenerError):
        links.add_link(spelling, DOCS)
    assert state(links) == before
    assert links.get_codes() == ["Promo", "docs"]


def test_every_lookup_ignores_case(links):
    assert links.visit("PROMO") == SALE
    assert links.visit("promo") == SALE
    assert links.get_hits("pRoMo") == 2
    assert links.get_target("PROMO") == SALE
    links.set_target("promo", "https://example.com/new")
    assert links.get_target("Promo") == "https://example.com/new"
    assert links.get_hits("Promo") == 2


def test_listings_keep_the_spelling_used_when_adding(links):
    links.add_link("BLOG-Posts", "https://example.com/blog")
    links.visit("blog-posts")
    links.visit("DOCS")
    links.visit("docs")
    assert links.get_codes() == ["Promo", "docs", "BLOG-Posts"]
    assert links.get_most_visited() == ["docs", "BLOG-Posts", "Promo"]


def test_unknown_codes_still_raise_key_error(links):
    for code in ["missing", "promo2", None, 1]:
        with pytest.raises(KeyError):
            links.visit(code)


@pytest.mark.parametrize("spelling", ["admin", "ADMIN", "Login", "login"])
def test_reserved_codes_are_refused_in_any_case(links, spelling):
    before = state(links)
    with pytest.raises(ReservedCode):
        links.add_link(spelling, SALE)
    assert state(links) == before
    assert links.get_codes() == ["Promo", "docs"]


def test_reserved_codes_are_not_links(links):
    assert links.get_codes() == ["Promo", "docs"]
    with pytest.raises(KeyError):
        links.get_target("admin")


def test_no_reserved_codes_by_default():
    sh = Shortener()
    sh.add_link("admin", SALE)
    assert sh.get_codes() == ["admin"]


@pytest.mark.parametrize("bad", BAD_CODES)
def test_invalid_reserved_entries_are_rejected(bad):
    with pytest.raises(ValueError):
        Shortener(reserved=("admin", bad))


def test_reserved_code_is_a_shortener_error():
    assert issubclass(ReservedCode, ShortenerError)


def test_error_order_when_adding(links):
    with pytest.raises(ValueError):
        links.add_link("bad code", "")  # bad code before bad target
    with pytest.raises(ValueError):
        links.add_link("admin", "")  # bad target before reserved
    with pytest.raises(ValueError):
        links.add_link("promo", "")  # bad target before duplicate
    with pytest.raises(ReservedCode):
        links.add_link("ADMIN", SALE)
    assert links.get_codes() == ["Promo", "docs"]
