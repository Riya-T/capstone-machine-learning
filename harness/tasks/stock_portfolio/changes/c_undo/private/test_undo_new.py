"""Hidden tests for the c_undo change (cancelling the last trade). Never shown
to the writer or the editor.

Usage (with portfolio.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from portfolio import InsufficientShares, Portfolio, PortfolioError


@pytest.fixture
def folio():
    pf = Portfolio()
    pf.deposit_cash(100_000)
    return pf


def state(pf):
    return (pf.get_cash(), {s: pf.get_shares(s) for s in pf.get_holdings()}, pf.get_trades())


def test_cancelling_a_buy_restores_the_state_before_it(folio):
    folio.buy("ACME", 10, 1_000)
    before = state(folio)
    folio.buy("BOLT", 3, 2_000)
    assert folio.cancel_last_trade() == ("buy", "BOLT", 3, 2_000)
    assert state(folio) == before
    assert folio.get_shares("BOLT") == 0


def test_cancelling_a_sell_restores_the_state_before_it(folio):
    folio.buy("ACME", 10, 1_000)
    before = state(folio)
    folio.sell("ACME", 10, 5_000)
    assert folio.get_holdings() == []
    assert folio.cancel_last_trade() == ("sell", "ACME", 10, 5_000)
    assert state(folio) == before
    assert folio.get_holdings() == ["ACME"]


def test_cancelling_a_partial_buy_keeps_the_earlier_shares(folio):
    folio.buy("ACME", 10, 1_000)
    folio.buy("ACME", 5, 1_200)
    folio.cancel_last_trade()
    assert folio.get_shares("ACME") == 10
    assert folio.get_cash() == 90_000
    assert folio.get_holdings() == ["ACME"]


def test_repeated_cancels_walk_back_through_the_trades(folio):
    folio.buy("ACME", 10, 1_000)
    folio.buy("BOLT", 2, 500)
    folio.sell("ACME", 4, 1_500)
    assert folio.cancel_last_trade() == ("sell", "ACME", 4, 1_500)
    assert folio.cancel_last_trade() == ("buy", "BOLT", 2, 500)
    assert folio.get_trades() == [("buy", "ACME", 10, 1_000)]
    assert folio.get_cash() == 90_000
    assert folio.get_holdings() == ["ACME"]
    assert folio.cancel_last_trade() == ("buy", "ACME", 10, 1_000)
    assert state(folio) == (100_000, {}, [])


def test_cancelling_with_no_trades_raises_and_changes_nothing(folio):
    before = state(folio)
    with pytest.raises(PortfolioError):
        folio.cancel_last_trade()
    assert state(folio) == before


def test_cancelling_every_trade_then_one_more_raises(folio):
    folio.buy("ACME", 1, 1_000)
    folio.cancel_last_trade()
    with pytest.raises(PortfolioError):
        folio.cancel_last_trade()
    assert state(folio) == (100_000, {}, [])


def test_a_cancelled_sell_restores_the_holdings_order(folio):
    folio.buy("ACME", 1, 1_000)
    folio.buy("BOLT", 1, 1_000)
    folio.buy("CORE", 1, 1_000)
    folio.sell("BOLT", 1, 1_000)
    assert folio.get_holdings() == ["ACME", "CORE"]
    folio.cancel_last_trade()
    assert folio.get_holdings() == ["ACME", "BOLT", "CORE"]


def test_deposits_are_not_cancelled(folio):
    folio.buy("ACME", 10, 1_000)
    folio.deposit_cash(5_000)
    assert folio.cancel_last_trade() == ("buy", "ACME", 10, 1_000)
    assert folio.get_cash() == 105_000
    assert folio.get_trades() == []


def test_a_failed_trade_cannot_be_cancelled(folio):
    folio.buy("ACME", 1, 1_000)
    with pytest.raises(InsufficientShares):
        folio.sell("ACME", 2, 1_000)
    assert folio.cancel_last_trade() == ("buy", "ACME", 1, 1_000)
    with pytest.raises(PortfolioError):
        folio.cancel_last_trade()


def test_trading_continues_normally_after_a_cancel(folio):
    folio.buy("ACME", 10, 1_000)
    folio.cancel_last_trade()
    folio.buy("BOLT", 4, 2_000)
    folio.sell("BOLT", 1, 2_500)
    assert folio.get_cash() == 100_000 - 8_000 + 2_500
    assert folio.get_holdings() == ["BOLT"]
    assert folio.get_trades() == [("buy", "BOLT", 4, 2_000), ("sell", "BOLT", 1, 2_500)]


def test_the_returned_trade_is_a_tuple(folio):
    folio.buy("ACME", 2, 300)
    cancelled = folio.cancel_last_trade()
    assert isinstance(cancelled, tuple)
    assert cancelled == ("buy", "ACME", 2, 300)
