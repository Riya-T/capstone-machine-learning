"""Hidden tests for the initial stock_portfolio spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with portfolio.py importable, e.g. in the sandbox):
    python -m pytest private/test_portfolio_initial.py
"""

import pytest
from portfolio import InsufficientCash, InsufficientShares, Portfolio, PortfolioError

BAD_INTS = [0, -5, 1.5, "10", None]
BAD_SYMBOLS = ["", None, 7]


@pytest.fixture
def folio():
    pf = Portfolio()
    pf.deposit_cash(100_000)
    return pf


def state(pf):
    """Cash, every holding and the trades, to check that a failed call changed nothing."""
    return (pf.get_cash(), {s: pf.get_shares(s) for s in pf.get_holdings()}, pf.get_trades())


# --- cash -------------------------------------------------------------------


def test_a_new_portfolio_is_empty():
    pf = Portfolio()
    assert pf.get_cash() == 0
    assert pf.get_holdings() == []
    assert pf.get_trades() == []
    assert pf.get_shares("ACME") == 0


def test_deposits_add_up():
    pf = Portfolio()
    pf.deposit_cash(500)
    pf.deposit_cash(250)
    assert pf.get_cash() == 750
    assert pf.get_trades() == []


@pytest.mark.parametrize("amount", BAD_INTS)
def test_invalid_deposits_are_rejected(folio, amount):
    before = state(folio)
    with pytest.raises(ValueError):
        folio.deposit_cash(amount)
    assert state(folio) == before


# --- trading ----------------------------------------------------------------


def test_buying_takes_the_cost_and_adds_the_shares(folio):
    folio.buy("ACME", 10, 2_500)
    folio.buy("ACME", 5, 2_000)
    assert folio.get_cash() == 65_000
    assert folio.get_shares("ACME") == 15


def test_all_the_cash_can_be_spent(folio):
    folio.buy("ACME", 40, 2_500)
    assert folio.get_cash() == 0
    assert folio.get_shares("ACME") == 40


def test_buying_more_than_the_cash_raises_and_changes_nothing(folio):
    before = state(folio)
    with pytest.raises(InsufficientCash):
        folio.buy("ACME", 1, 100_001)
    with pytest.raises(InsufficientCash):
        folio.buy("ACME", 101, 1_000)
    assert state(folio) == before


def test_selling_adds_the_proceeds_and_removes_the_shares(folio):
    folio.buy("ACME", 10, 2_500)
    folio.sell("ACME", 3, 3_000)
    assert folio.get_cash() == 84_000
    assert folio.get_shares("ACME") == 7


def test_all_the_shares_can_be_sold(folio):
    folio.buy("ACME", 10, 2_500)
    folio.sell("ACME", 10, 1_000)
    assert folio.get_shares("ACME") == 0
    assert folio.get_cash() == 85_000
    assert folio.get_holdings() == []


def test_selling_more_than_held_raises_and_changes_nothing(folio):
    folio.buy("ACME", 10, 2_500)
    before = state(folio)
    with pytest.raises(InsufficientShares):
        folio.sell("ACME", 11, 100)
    assert state(folio) == before


def test_selling_a_symbol_never_bought_raises(folio):
    before = state(folio)
    with pytest.raises(InsufficientShares):
        folio.sell("BOLT", 1, 100)
    assert state(folio) == before


def test_selling_can_only_use_shares_of_the_same_symbol(folio):
    folio.buy("ACME", 10, 1_000)
    with pytest.raises(InsufficientShares):
        folio.sell("BOLT", 1, 1_000)
    assert folio.get_shares("ACME") == 10


@pytest.mark.parametrize("symbol", BAD_SYMBOLS)
@pytest.mark.parametrize(
    "call",
    [
        lambda pf, s: pf.buy(s, 1, 100),
        lambda pf, s: pf.sell(s, 1, 100),
        lambda pf, s: pf.get_shares(s),
    ],
    ids=["buy", "sell", "get_shares"],
)
def test_invalid_symbols_are_rejected(folio, call, symbol):
    folio.buy("ACME", 1, 100)
    before = state(folio)
    with pytest.raises(ValueError):
        call(folio, symbol)
    assert state(folio) == before


@pytest.mark.parametrize("bad", BAD_INTS)
@pytest.mark.parametrize(
    "call",
    [
        lambda pf, b: pf.buy("ACME", b, 100),
        lambda pf, b: pf.buy("ACME", 1, b),
        lambda pf, b: pf.sell("ACME", b, 100),
        lambda pf, b: pf.sell("ACME", 1, b),
    ],
    ids=["buy-shares", "buy-price", "sell-shares", "sell-price"],
)
def test_invalid_shares_and_prices_are_rejected(folio, call, bad):
    folio.buy("ACME", 5, 100)
    before = state(folio)
    with pytest.raises(ValueError):
        call(folio, bad)
    assert state(folio) == before


def test_a_bad_symbol_is_reported_before_bad_shares(folio):
    with pytest.raises(ValueError):
        folio.buy("", 0, 100)


def test_bad_input_is_reported_before_missing_cash():
    pf = Portfolio()  # no cash at all
    with pytest.raises(ValueError):
        pf.buy("ACME", 1, 1.5)
    with pytest.raises(ValueError):
        pf.buy("ACME", -1, 100)
    with pytest.raises(ValueError):
        pf.buy(None, 1, 100)


def test_bad_input_is_reported_before_missing_shares(folio):
    with pytest.raises(ValueError):
        folio.sell("ACME", 1, 0)
    with pytest.raises(ValueError):
        folio.sell("ACME", "3", 100)


# --- holdings and trades ----------------------------------------------------


def test_holdings_are_listed_in_the_order_first_bought(folio):
    folio.buy("CORE", 1, 100)
    folio.buy("ACME", 1, 100)
    folio.buy("BOLT", 1, 100)
    folio.buy("ACME", 1, 100)
    assert folio.get_holdings() == ["CORE", "ACME", "BOLT"]


def test_a_symbol_sold_out_leaves_the_holdings(folio):
    folio.buy("ACME", 2, 100)
    folio.buy("BOLT", 2, 100)
    folio.buy("CORE", 2, 100)
    folio.sell("BOLT", 2, 100)
    assert folio.get_holdings() == ["ACME", "CORE"]
    assert folio.get_shares("BOLT") == 0
    folio.sell("ACME", 1, 100)
    assert folio.get_holdings() == ["ACME", "CORE"]


def test_trades_record_every_buy_and_sell(folio):
    folio.buy("ACME", 10, 2_500)
    folio.sell("ACME", 4, 3_000)
    folio.buy("BOLT", 1, 999)
    folio.deposit_cash(1)
    assert folio.get_trades() == [
        ("buy", "ACME", 10, 2_500),
        ("sell", "ACME", 4, 3_000),
        ("buy", "BOLT", 1, 999),
    ]


def test_failed_calls_add_no_trades(folio):
    folio.buy("ACME", 1, 100)
    for call in (
        lambda: folio.buy("ACME", 1, 200_000),
        lambda: folio.sell("ACME", 2, 100),
        lambda: folio.buy("ACME", 0, 100),
        lambda: folio.sell("", 1, 100),
    ):
        with pytest.raises((ValueError, PortfolioError)):
            call()
    assert folio.get_trades() == [("buy", "ACME", 1, 100)]


def test_errors_are_portfolio_errors():
    assert issubclass(InsufficientCash, PortfolioError)
    assert issubclass(InsufficientShares, PortfolioError)
    assert not issubclass(InsufficientCash, InsufficientShares)
    assert not issubclass(InsufficientShares, InsufficientCash)


def test_portfolios_do_not_share_state():
    first, second = Portfolio(), Portfolio()
    first.deposit_cash(1_000)
    first.buy("ACME", 1, 100)
    assert second.get_cash() == 0
    assert second.get_holdings() == []
    assert second.get_trades() == []
