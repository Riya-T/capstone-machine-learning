"""Hidden tests for the c_disable change (disabled links). Never shown to the
writer or the editor.

Usage (with shortener.py importable, e.g. in the sandbox):
    python -m pytest changes/c_disable/private/test_disable_new.py
"""

import pytest
from shortener import LinkDisabled, Shortener, ShortenerError

SALE = "https://example.com/sale"
DOCS = "https://example.com/docs"


@pytest.fixture
def links():
    sh = Shortener()
    sh.add_link("promo", SALE)
    sh.add_link("docs", DOCS)
    sh.visit("promo")
    return sh


def state(sh):
    return {c: (sh.get_target(c), sh.get_hits(c), sh.is_enabled(c)) for c in sh.get_codes()}


def test_new_links_are_enabled(links):
    assert links.is_enabled("promo")
    assert links.is_enabled("docs")


def test_disabling_or_enabling_twice_is_harmless(links):
    links.disable("promo")
    links.disable("promo")
    assert not links.is_enabled("promo")
    assert links.is_enabled("docs")
    links.enable("promo")
    links.enable("promo")
    assert links.is_enabled("promo")


@pytest.mark.parametrize("method", ["disable", "enable", "is_enabled"])
@pytest.mark.parametrize("code", ["missing", None, 1])
def test_switching_a_missing_code_raises_key_error(links, method, code):
    before = state(links)
    with pytest.raises(KeyError):
        getattr(links, method)(code)
    assert state(links) == before


def test_a_visit_to_a_disabled_link_changes_nothing(links):
    links.disable("promo")
    before = state(links)
    with pytest.raises(LinkDisabled):
        links.visit("promo")
    assert state(links) == before
    assert links.get_hits("promo") == 1


def test_a_missing_code_is_reported_before_disabled(links):
    links.disable("promo")
    with pytest.raises(KeyError):
        links.visit("missing")


def test_disabled_links_keep_their_target_and_hits(links):
    links.disable("promo")
    assert links.get_target("promo") == SALE
    assert links.get_hits("promo") == 1
    links.set_target("promo", "https://example.com/new")
    assert links.get_target("promo") == "https://example.com/new"
    assert not links.is_enabled("promo")
    links.enable("promo")
    assert links.visit("promo") == "https://example.com/new"


def test_disabled_links_stay_in_the_listings(links):
    links.disable("promo")
    assert links.get_codes() == ["promo", "docs"]
    assert links.get_most_visited() == ["promo", "docs"]
    links.visit("docs")
    links.visit("docs")
    assert links.get_most_visited() == ["docs", "promo"]


def test_other_links_are_not_affected(links):
    links.disable("promo")
    assert links.visit("docs") == DOCS
    assert links.get_hits("docs") == 1
    assert links.is_enabled("docs")


def test_an_enabled_link_counts_hits_again(links):
    links.disable("promo")
    links.enable("promo")
    links.visit("promo")
    links.visit("promo")
    assert links.get_hits("promo") == 3


def test_link_disabled_is_a_shortener_error():
    assert issubclass(LinkDisabled, ShortenerError)


def test_shorteners_do_not_share_disabled_links(links):
    links.disable("promo")
    other = Shortener()
    other.add_link("promo", SALE)
    assert other.is_enabled("promo")
    assert other.visit("promo") == SALE
