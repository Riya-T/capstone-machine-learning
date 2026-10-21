"""Hidden tests for the c_stats change (hit statistics). Never shown to the
writer or the editor.

Usage (with shortener.py importable, e.g. in the sandbox):
    python -m pytest changes/c_stats/private/test_stats_new.py
"""

import pytest
from shortener import Shortener

SALE = "https://example.com/sale"
DOCS = "https://example.com/docs"
NEW = "https://example.com/new"


@pytest.fixture
def links():
    sh = Shortener()
    sh.add_link("promo", SALE)
    sh.add_link("docs", DOCS)
    sh.add_link("blog", "https://example.com/blog")
    return sh


def test_a_fresh_shortener_has_no_hits(links):
    assert links.get_total_hits() == 0
    assert links.get_unvisited() == ["promo", "docs", "blog"]
    assert links.get_target_hits(SALE) == 0
    assert links.get_hits_for_current_target("promo") == 0


def test_total_hits_adds_up_over_all_codes(links):
    for code in ["promo", "docs", "promo", "blog", "promo"]:
        links.visit(code)
    assert links.get_total_hits() == 5
    assert links.get_unvisited() == []


def test_unvisited_keeps_the_added_order(links):
    links.visit("docs")
    assert links.get_unvisited() == ["promo", "blog"]
    links.visit("blog")
    assert links.get_unvisited() == ["promo"]


def test_target_hits_follow_the_target_served_at_the_time(links):
    links.visit("promo")
    links.visit("promo")
    links.set_target("promo", NEW)
    links.visit("promo")
    assert links.get_target_hits(SALE) == 2
    assert links.get_target_hits(NEW) == 1
    assert links.get_hits("promo") == 3


def test_target_hits_add_up_over_codes_sharing_a_target(links):
    links.set_target("docs", SALE)
    links.visit("promo")
    links.visit("docs")
    links.visit("docs")
    assert links.get_target_hits(SALE) == 3
    assert links.get_target_hits(DOCS) == 0


@pytest.mark.parametrize("bad_target", ["", None, 7])
def test_target_hits_rejects_invalid_targets(links, bad_target):
    with pytest.raises(ValueError):
        links.get_target_hits(bad_target)


def test_current_target_hits_restart_on_every_set_target(links):
    links.visit("promo")
    links.visit("promo")
    links.set_target("promo", NEW)
    assert links.get_hits_for_current_target("promo") == 0
    links.visit("promo")
    links.visit("promo")
    links.visit("promo")
    assert links.get_hits_for_current_target("promo") == 3
    links.set_target("promo", NEW)  # the same target still restarts the count
    assert links.get_hits_for_current_target("promo") == 0
    assert links.get_hits("promo") == 5


def test_current_target_hits_without_set_target_equal_all_hits(links):
    links.visit("docs")
    links.visit("docs")
    assert links.get_hits_for_current_target("docs") == 2
    assert links.get_hits_for_current_target("blog") == 0


def test_a_failed_set_target_does_not_restart_the_count(links):
    links.visit("promo")
    with pytest.raises(ValueError):
        links.set_target("promo", "")
    assert links.get_hits_for_current_target("promo") == 1


@pytest.mark.parametrize("code", ["missing", None, 1])
def test_current_target_hits_of_a_missing_code_raises_key_error(links, code):
    with pytest.raises(KeyError):
        links.get_hits_for_current_target(code)


def test_failed_visits_count_for_nothing(links):
    links.visit("promo")
    with pytest.raises(KeyError):
        links.visit("missing")
    assert links.get_total_hits() == 1
    assert links.get_target_hits(SALE) == 1
    assert links.get_unvisited() == ["docs", "blog"]


def test_statistics_are_per_shortener(links):
    links.visit("promo")
    other = Shortener()
    other.add_link("promo", SALE)
    assert other.get_total_hits() == 0
    assert other.get_target_hits(SALE) == 0
    assert other.get_unvisited() == ["promo"]
