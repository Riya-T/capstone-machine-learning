"""Public checks for the c_disable change (disabled links). Shown to the
editor, never to the writer.

Usage (with shortener.py importable, e.g. in the sandbox):
    python -m pytest changes/c_disable/public/test_disable_public.py
"""

import pytest
from shortener import LinkDisabled, Shortener


def test_a_disabled_link_refuses_visits_until_enabled():
    sh = Shortener()
    sh.add_link("promo", "https://example.com/sale")
    sh.visit("promo")
    sh.disable("promo")
    assert not sh.is_enabled("promo")
    with pytest.raises(LinkDisabled):
        sh.visit("promo")
    assert sh.get_hits("promo") == 1
    sh.enable("promo")
    assert sh.visit("promo") == "https://example.com/sale"
    assert sh.get_hits("promo") == 2


def test_disabled_links_still_report_their_target():
    sh = Shortener()
    sh.add_link("promo", "https://example.com/sale")
    sh.disable("promo")
    assert sh.get_target("promo") == "https://example.com/sale"
    assert sh.get_codes() == ["promo"]
