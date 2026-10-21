"""Hidden tests for the initial url_shortener spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with shortener.py importable, e.g. in the sandbox):
    python -m pytest private/test_shortener_initial.py
"""

import pytest
from shortener import Shortener, ShortenerError

BAD_TEXT = ["", None, 7]
SALE = "https://example.com/sale"
DOCS = "https://example.com/docs"


@pytest.fixture
def links():
    sh = Shortener()
    sh.add_link("promo", SALE)
    sh.add_link("docs", DOCS)
    return sh


def state(sh):
    """Every target and hit count, to check that a failed call changed nothing."""
    return {c: (sh.get_target(c), sh.get_hits(c)) for c in sh.get_codes()}


# --- links ------------------------------------------------------------------


def test_a_new_link_points_at_its_target_with_no_hits(links):
    assert links.get_target("promo") == SALE
    assert links.get_hits("promo") == 0


def test_codes_are_listed_in_the_order_added():
    sh = Shortener()
    for code in ["zeta", "alpha", "mid"]:
        sh.add_link(code, SALE)
    assert sh.get_codes() == ["zeta", "alpha", "mid"]


@pytest.mark.parametrize("bad_code", BAD_TEXT)
def test_invalid_codes_are_rejected(bad_code):
    sh = Shortener()
    with pytest.raises(ValueError):
        sh.add_link(bad_code, SALE)
    assert sh.get_codes() == []


@pytest.mark.parametrize("bad_target", BAD_TEXT)
def test_invalid_targets_are_rejected_when_adding(links, bad_target):
    before = state(links)
    with pytest.raises(ValueError):
        links.add_link("news", bad_target)
    assert links.get_codes() == ["promo", "docs"]
    assert state(links) == before


def test_adding_an_existing_code_is_rejected_and_changes_nothing(links):
    links.visit("promo")
    before = state(links)
    with pytest.raises(ShortenerError):
        links.add_link("promo", DOCS)
    assert state(links) == before
    assert links.get_codes() == ["promo", "docs"]


@pytest.mark.parametrize(
    "call",
    [
        lambda sh: sh.visit("missing"),
        lambda sh: sh.get_target("missing"),
        lambda sh: sh.get_hits("missing"),
        lambda sh: sh.set_target("missing", SALE),
        lambda sh: sh.visit(None),
        lambda sh: sh.get_target(1),
        lambda sh: sh.set_target(None, SALE),
    ],
)
def test_codes_that_do_not_exist_raise_key_error(links, call):
    links.visit("promo")
    before = state(links)
    with pytest.raises(KeyError):
        call(links)
    assert state(links) == before


def test_set_target_keeps_the_hits(links):
    links.visit("promo")
    links.visit("promo")
    links.set_target("promo", "https://example.com/new")
    assert links.get_target("promo") == "https://example.com/new"
    assert links.get_hits("promo") == 2
    assert links.get_target("docs") == DOCS


@pytest.mark.parametrize("bad_target", BAD_TEXT)
def test_invalid_targets_are_rejected_when_setting(links, bad_target):
    links.visit("promo")
    before = state(links)
    with pytest.raises(ValueError):
        links.set_target("promo", bad_target)
    assert state(links) == before


def test_a_missing_code_is_reported_before_a_bad_target(links):
    with pytest.raises(KeyError):
        links.set_target("missing", "")


def test_a_bad_code_is_reported_before_a_bad_target():
    sh = Shortener()
    with pytest.raises(ValueError):
        sh.add_link("", "")
    assert sh.get_codes() == []


# --- visits -----------------------------------------------------------------


def test_visits_accumulate_per_code(links):
    for _ in range(3):
        links.visit("promo")
    links.visit("docs")
    assert links.get_hits("promo") == 3
    assert links.get_hits("docs") == 1


def test_visit_returns_the_current_target(links):
    assert links.visit("promo") == SALE
    links.set_target("promo", "https://example.com/new")
    assert links.visit("promo") == "https://example.com/new"
    assert links.get_hits("promo") == 2


def test_failed_visits_count_nothing(links):
    with pytest.raises(KeyError):
        links.visit("missing")
    assert links.get_hits("promo") == 0
    assert links.get_hits("docs") == 0


def test_most_visited_orders_by_hits_highest_first(links):
    links.add_link("blog", "https://example.com/blog")
    for code, times in [("promo", 1), ("docs", 3), ("blog", 2)]:
        for _ in range(times):
            links.visit(code)
    assert links.get_most_visited() == ["docs", "blog", "promo"]


def test_most_visited_breaks_ties_by_the_order_added(links):
    links.add_link("blog", "https://example.com/blog")
    links.add_link("shop", "https://example.com/shop")
    links.visit("shop")
    links.visit("docs")
    assert links.get_most_visited() == ["docs", "shop", "promo", "blog"]


def test_most_visited_with_no_hits_is_the_added_order(links):
    links.add_link("blog", "https://example.com/blog")
    assert links.get_most_visited() == ["promo", "docs", "blog"]


def test_most_visited_follows_later_visits(links):
    links.visit("docs")
    assert links.get_most_visited() == ["docs", "promo"]
    links.visit("promo")
    links.visit("promo")
    assert links.get_most_visited() == ["promo", "docs"]


def test_most_visited_of_an_empty_shortener_is_empty():
    assert Shortener().get_most_visited() == []
    assert Shortener().get_codes() == []


def test_shorteners_do_not_share_links():
    first, second = Shortener(), Shortener()
    first.add_link("promo", SALE)
    first.visit("promo")
    assert second.get_codes() == []
    second.add_link("promo", DOCS)
    assert second.get_hits("promo") == 0
    assert second.get_target("promo") == DOCS
