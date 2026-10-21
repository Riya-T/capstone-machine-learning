"""Public checks for shortener.py.

Usage (with shortener.py importable, e.g. in the sandbox):
    python -m pytest public/test_shortener_public.py
"""

import pytest
from shortener import Shortener, ShortenerError


@pytest.fixture
def links():
    sh = Shortener()
    sh.add_link("promo", "https://example.com/sale")
    sh.add_link("docs", "https://example.com/docs")
    return sh


def test_visit_returns_the_target_and_counts_a_hit(links):
    assert links.visit("promo") == "https://example.com/sale"
    assert links.visit("promo") == "https://example.com/sale"
    assert links.get_hits("promo") == 2
    assert links.get_hits("docs") == 0


def test_set_target_changes_where_a_code_points(links):
    links.visit("promo")
    links.set_target("promo", "https://example.com/autumn")
    assert links.get_target("promo") == "https://example.com/autumn"
    assert links.visit("promo") == "https://example.com/autumn"
    assert links.get_hits("promo") == 2


def test_most_visited_lists_every_code_highest_first(links):
    links.add_link("blog", "https://example.com/blog")
    links.visit("docs")
    links.visit("docs")
    links.visit("blog")
    assert links.get_most_visited() == ["docs", "blog", "promo"]
    assert links.get_codes() == ["promo", "docs", "blog"]


def test_a_code_that_does_not_exist_raises_key_error(links):
    with pytest.raises(KeyError):
        links.visit("missing")
    with pytest.raises(KeyError):
        links.get_hits("missing")


def test_codes_and_targets_must_not_be_empty(links):
    with pytest.raises(ValueError):
        links.add_link("", "https://example.com")
    with pytest.raises(ValueError):
        links.add_link("news", "")
    assert links.get_codes() == ["promo", "docs"]


def test_adding_an_existing_code_raises_shortener_error(links):
    with pytest.raises(ShortenerError):
        links.add_link("promo", "https://example.com/other")
    assert links.get_target("promo") == "https://example.com/sale"
