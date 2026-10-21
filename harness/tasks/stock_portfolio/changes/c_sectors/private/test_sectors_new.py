"""Hidden tests for the c_sectors change (sectors). Never shown to the
writer or the editor.

Usage (with portfolio.py importable, e.g. in the sandbox):
    python -m pytest changes/c_sectors/private/test_sectors_new.py
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


def state(pf):
    return (pf.get_cash(), {s: pf.get_shares(s) for s in pf.get_holdings()}, pf.get_trades())


def test_symbols_start_without_a_sector(folio):
    assert folio.get_sectors() == []
    with pytest.raises(KeyError):
        folio.get_sector("ACME")


def test_set_sector_and_get_sector_round_trip(folio):
    folio.set_sector("ACME", "industrials")
    folio.set_sector("BOLT", "tech")
    assert folio.get_sector("ACME") == "industrials"
    assert folio.get_sector("BOLT") == "tech"
    with pytest.raises(KeyError):
        folio.get_sector("CORE")


def test_sectors_are_listed_in_the_order_first_used(folio):
    folio.set_sector("CORE", "energy")
    folio.set_sector("ACME", "industrials")
    folio.set_sector("BOLT", "energy")
    assert folio.get_sectors() == ["energy", "industrials"]


def test_setting_a_sector_again_replaces_it(folio):
    folio.set_sector("ACME", "industrials")
    folio.set_sector("ACME", "tech")
    assert folio.get_sector("ACME") == "tech"
    assert folio.get_sectors() == ["tech"]
    with pytest.raises(KeyError):
        folio.get_sector_holdings("industrials")


def test_a_sector_can_be_set_for_a_symbol_not_held(folio):
    folio.set_sector("DELTA", "energy")
    assert folio.get_sector("DELTA") == "energy"
    assert folio.get_sectors() == ["energy"]
    assert folio.get_sector_holdings("energy") == []


def test_sector_holdings_follow_the_holdings_order(folio):
    folio.set_sector("CORE", "industrials")
    folio.set_sector("ACME", "industrials")
    folio.set_sector("BOLT", "industrials")
    assert folio.get_sector_holdings("industrials") == ["ACME", "BOLT", "CORE"]


def test_sector_holdings_leave_out_other_sectors_and_unsectored_symbols(folio):
    folio.set_sector("ACME", "industrials")
    folio.set_sector("BOLT", "tech")
    assert folio.get_sector_holdings("industrials") == ["ACME"]
    assert folio.get_sector_holdings("tech") == ["BOLT"]


def test_a_symbol_sold_out_leaves_its_sector_holdings(folio):
    folio.set_sector("ACME", "industrials")
    folio.set_sector("CORE", "industrials")
    folio.sell("ACME", 10, 1_000)
    assert folio.get_sector_holdings("industrials") == ["CORE"]
    assert folio.get_sector("ACME") == "industrials"
    assert folio.get_sectors() == ["industrials"]
    folio.sell("CORE", 2, 1_000)
    assert folio.get_sector_holdings("industrials") == []


def test_buying_later_adds_to_sector_holdings(folio):
    folio.set_sector("DELTA", "energy")
    folio.buy("DELTA", 1, 1_000)
    assert folio.get_sector_holdings("energy") == ["DELTA"]


@pytest.mark.parametrize("sector", ["", None, 3])
def test_invalid_sector_names_are_rejected(folio, sector):
    with pytest.raises(ValueError):
        folio.set_sector("ACME", sector)
    assert folio.get_sectors() == []


@pytest.mark.parametrize("symbol", ["", None, 7])
def test_invalid_symbols_are_rejected_by_sector_methods(folio, symbol):
    with pytest.raises(ValueError):
        folio.set_sector(symbol, "tech")
    with pytest.raises(ValueError):
        folio.get_sector(symbol)


def test_a_bad_symbol_is_reported_before_a_bad_sector(folio):
    with pytest.raises(ValueError):
        folio.set_sector("", "")
    with pytest.raises(ValueError):
        folio.set_sector(None, "")


def test_unknown_sectors_raise_key_error(folio):
    with pytest.raises(KeyError):
        folio.get_sector_holdings("tech")
    folio.set_sector("ACME", "tech")
    with pytest.raises(KeyError):
        folio.get_sector_holdings("energy")


def test_setting_sectors_changes_no_cash_shares_or_trades(folio):
    before = state(folio)
    folio.set_sector("ACME", "industrials")
    folio.set_sector("ACME", "tech")
    assert state(folio) == before
