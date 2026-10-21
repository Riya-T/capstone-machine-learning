"""Public checks for the c_undo change (cancelling the last trade). Shown to
the editor, never to the writer.

Usage (with portfolio.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from portfolio import Portfolio, PortfolioError


def test_cancelling_a_buy_gives_the_cash_back():
    pf = Portfolio()
    pf.deposit_cash(100_000)
    pf.buy("ACME", 10, 2_500)
    assert pf.cancel_last_trade() == ("buy", "ACME", 10, 2_500)
    assert pf.get_cash() == 100_000
    assert pf.get_shares("ACME") == 0
    assert pf.get_holdings() == []
    assert pf.get_trades() == []


def test_cancelling_a_sell_returns_the_shares():
    pf = Portfolio()
    pf.deposit_cash(100_000)
    pf.buy("ACME", 10, 2_500)
    pf.sell("ACME", 4, 3_000)
    assert pf.cancel_last_trade() == ("sell", "ACME", 4, 3_000)
    assert pf.get_cash() == 75_000
    assert pf.get_shares("ACME") == 10
    assert pf.get_trades() == [("buy", "ACME", 10, 2_500)]


def test_nothing_to_cancel_raises():
    pf = Portfolio()
    pf.deposit_cash(1_000)
    with pytest.raises(PortfolioError):
        pf.cancel_last_trade()
    assert pf.get_cash() == 1_000
