"""Public checks for the c_alias change (code rules). Shown to the editor,
never to the writer.

Usage (with shortener.py importable, e.g. in the sandbox):
    python -m pytest changes/c_alias/public/test_alias_public.py
"""

import pytest
from shortener import ReservedCode, Shortener, ShortenerError


def test_codes_match_without_regard_to_case():
    sh = Shortener()
    sh.add_link("Sale", "https://example.com/sale")
    assert sh.visit("SALE") == "https://example.com/sale"
    assert sh.get_hits("sale") == 1
    with pytest.raises(ShortenerError):
        sh.add_link("sale", "https://example.com/other")
    assert sh.get_codes() == ["Sale"]


def test_values_that_are_not_strings_are_unknown_codes():
    sh = Shortener()
    sh.add_link("Sale", "https://example.com/sale")
    with pytest.raises(KeyError):
        sh.visit(None)
    with pytest.raises(KeyError):
        sh.get_target(1)
    with pytest.raises(KeyError):
        sh.set_target(None, "https://example.com/other")
    assert sh.get_hits("SALE") == 0
    assert sh.get_target("sale") == "https://example.com/sale"


def test_codes_with_other_characters_are_rejected():
    sh = Shortener()
    with pytest.raises(ValueError):
        sh.add_link("spring sale", "https://example.com/sale")
    with pytest.raises(ValueError):
        sh.add_link("a" * 33, "https://example.com/sale")
    sh.add_link("spring-sale_2", "https://example.com/sale")
    assert sh.get_codes() == ["spring-sale_2"]


def test_reserved_codes_cannot_be_added():
    sh = Shortener(reserved=("admin", "login"))
    with pytest.raises(ReservedCode):
        sh.add_link("Admin", "https://example.com/admin")
    sh.add_link("help", "https://example.com/help")
    assert sh.get_codes() == ["help"]


def test_reserved_entries_must_be_valid_codes():
    with pytest.raises(ValueError):
        Shortener(reserved=("admin", "spring sale"))
    with pytest.raises(ValueError):
        Shortener(reserved=("admin", None))
