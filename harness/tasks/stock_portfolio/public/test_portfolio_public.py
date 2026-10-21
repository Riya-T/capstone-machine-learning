"""Public checks for portfolio.py.

Usage (with portfolio.py importable, e.g. in the sandbox):
    python -m pytest public/test_portfolio_public.py
"""

import pytest
from portfolio import InsufficientCash, InsufficientShares, Portfolio


@pytest.fixture
def folio():
    pf = Portfolio()
    pf.deposit_cash(100_000)
    return pf


def test_buying_takes_cash_and_adds_shares(folio):
    folio.buy("ACME", 10, 2_500)
    assert folio.get_cash() == 75_000
    assert folio.get_shares("ACME") == 10
    assert folio.get_holdings() == ["ACME"]


def test_selling_adds_cash_and_removes_shares(folio):
    folio.buy("ACME", 10, 2_500)
    folio.sell("ACME", 4, 3_000)
    assert folio.get_cash() == 87_000
    assert folio.get_shares("ACME") == 6


def test_buying_more_than_the_cash_raises(folio):
    with pytest.raises(InsufficientCash):
        folio.buy("ACME", 41, 2_500)
    assert folio.get_cash() == 100_000
    assert folio.get_shares("ACME") == 0


def test_selling_more_than_held_raises(folio):
    folio.buy("ACME", 3, 1_000)
    with pytest.raises(InsufficientShares):
        folio.sell("ACME", 4, 1_000)
    assert folio.get_shares("ACME") == 3


def test_trades_are_listed_oldest_first(folio):
    folio.buy("ACME", 10, 2_500)
    folio.buy("BOLT", 2, 400)
    folio.sell("ACME", 1, 2_600)
    assert folio.get_trades() == [
        ("buy", "ACME", 10, 2_500),
        ("buy", "BOLT", 2, 400),
        ("sell", "ACME", 1, 2_600),
    ]


def test_bad_inputs_raise_value_error(folio):
    with pytest.raises(ValueError):
        folio.deposit_cash(0)
    with pytest.raises(ValueError):
        folio.buy("", 1, 100)
    with pytest.raises(ValueError):
        folio.buy("ACME", 0, 100)
