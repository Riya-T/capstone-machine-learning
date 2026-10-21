"""Public checks for the c_stats change (hit statistics). Shown to the
editor, never to the writer.

Usage (with shortener.py importable, e.g. in the sandbox):
    python -m pytest changes/c_stats/public/test_stats_public.py
"""

from shortener import Shortener


def test_totals_and_unvisited_codes():
    sh = Shortener()
    sh.add_link("promo", "https://example.com/sale")
    sh.add_link("docs", "https://example.com/docs")
    sh.add_link("blog", "https://example.com/blog")
    sh.visit("promo")
    sh.visit("promo")
    sh.visit("blog")
    assert sh.get_total_hits() == 3
    assert sh.get_unvisited() == ["docs"]
    assert sh.get_target_hits("https://example.com/sale") == 2
    assert sh.get_target_hits("https://example.com/none") == 0


def test_hits_for_the_current_target_restart_after_set_target():
    sh = Shortener()
    sh.add_link("promo", "https://example.com/sale")
    sh.visit("promo")
    sh.visit("promo")
    sh.set_target("promo", "https://example.com/autumn")
    sh.visit("promo")
    assert sh.get_hits("promo") == 3
    assert sh.get_hits_for_current_target("promo") == 1
    assert sh.get_target_hits("https://example.com/sale") == 2
    assert sh.get_target_hits("https://example.com/autumn") == 1
