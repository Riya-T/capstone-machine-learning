"""Public checks for the c_sectors change (sectors). Shown to the editor,
never to the writer.

Usage (with portfolio.py importable, e.g. in the sandbox):
    python -m pytest changes/c_sectors/public/test_sectors_public.py
"""

import pytest
from portfolio import Portfolio


@pytest.fixture
def folio():
    pf = Portfolio()
    pf.deposit_cash(100_000)
    pf.buy("ACME", 10, 1_000)
    pf.buy("BOLT", 5, 1_000)
    pf.buy("CORE", 2, 1_000)
    return pf


def test_sector_holdings_list_held_symbols_in_that_sector(folio):
    folio.set_sector("ACME", "industrials")
    folio.set_sector("BOLT", "tech")
    folio.set_sector("CORE", "industrials")
    assert folio.get_sector("ACME") == "industrials"
    assert folio.get_sectors() == ["industrials", "tech"]
    assert folio.get_sector_holdings("industrials") == ["ACME", "CORE"]
    assert folio.get_sector_holdings("tech") == ["BOLT"]


def test_a_sector_nobody_uses_raises_key_error(folio):
    folio.set_sector("ACME", "industrials")
    with pytest.raises(KeyError):
        folio.get_sector_holdings("energy")
    with pytest.raises(KeyError):
        folio.get_sector("BOLT")


def test_an_empty_sector_name_is_rejected(folio):
    with pytest.raises(ValueError):
        folio.set_sector("ACME", "")
    assert folio.get_sectors() == []
