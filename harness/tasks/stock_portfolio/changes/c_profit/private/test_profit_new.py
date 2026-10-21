"""Hidden tests for the c_profit change (realized profit). Never shown to the
writer or the editor.

Usage (with portfolio.py importable, e.g. in the sandbox):
    python -m pytest changes/c_profit/private/test_profit_new.py
"""

import pytest
from portfolio import InsufficientCash, InsufficientShares, Portfolio


@pytest.fixture
def folio():
    pf = Portfolio()
    pf.deposit_cash(1_000_000)
    return pf


def test_a_new_portfolio_has_no_profit_and_no_cost_basis(folio):
    assert folio.get_realized_profit() == 0
    assert folio.get_realized_profit("ACME") == 0
    assert folio.get_cost_basis("ACME") == 0


def test_buying_sets_the_cost_basis_without_profit(folio):
    folio.buy("ACME", 10, 2_000)
    folio.buy("ACME", 5, 3_000)
    assert folio.get_cost_basis("ACME") == 35_000
    assert folio.get_realized_profit("ACME") == 0
    assert folio.get_realized_profit() == 0


def test_a_sale_at_a_higher_price_realizes_a_gain(folio):
    folio.buy("ACME", 10, 2_000)
    folio.sell("ACME", 3, 2_500)
    assert folio.get_realized_profit("ACME") == 1_500
    assert folio.get_cost_basis("ACME") == 14_000


def test_a_sale_at_a_lower_price_realizes_a_loss(folio):
    folio.buy("ACME", 10, 2_000)
    folio.sell("ACME", 4, 1_500)
    assert folio.get_realized_profit("ACME") == -2_000
    assert folio.get_realized_profit() == -2_000


def test_sales_take_the_oldest_shares_first(folio):
    folio.buy("ACME", 4, 1_000)
    folio.buy("ACME", 4, 2_000)
    folio.buy("ACME", 4, 3_000)
    folio.sell("ACME", 6, 2_500)
    # 4 at 1_000 then 2 at 2_000.
    assert folio.get_realized_profit("ACME") == 4 * 1_500 + 2 * 500
    assert folio.get_cost_basis("ACME") == 2 * 2_000 + 4 * 3_000
    folio.sell("ACME", 3, 2_500)
    # 2 at 2_000 then 1 at 3_000.
    assert folio.get_realized_profit("ACME") == 7_000 + 2 * 500 - 500
    assert folio.get_cost_basis("ACME") == 3 * 3_000


def test_profit_adds_up_over_several_sales(folio):
    folio.buy("ACME", 10, 1_000)
    folio.sell("ACME", 2, 1_200)
    folio.sell("ACME", 3, 900)
    folio.sell("ACME", 5, 1_000)
    assert folio.get_realized_profit("ACME") == 400 - 300 + 0
    assert folio.get_cost_basis("ACME") == 0
    assert folio.get_shares("ACME") == 0


def test_profit_is_kept_per_symbol_and_summed_overall(folio):
    folio.buy("ACME", 10, 1_000)
    folio.buy("BOLT", 10, 5_000)
    folio.sell("ACME", 10, 1_100)
    folio.sell("BOLT", 2, 4_000)
    assert folio.get_realized_profit("ACME") == 1_000
    assert folio.get_realized_profit("BOLT") == -2_000
    assert folio.get_realized_profit() == -1_000
    assert folio.get_cost_basis("BOLT") == 40_000


def test_rebuying_after_selling_out_starts_a_new_lot(folio):
    folio.buy("ACME", 5, 1_000)
    folio.sell("ACME", 5, 2_000)
    folio.buy("ACME", 2, 3_000)
    assert folio.get_cost_basis("ACME") == 6_000
    folio.sell("ACME", 1, 2_500)
    assert folio.get_realized_profit("ACME") == 5_000 - 500
    assert folio.get_cost_basis("ACME") == 3_000


def test_deposits_and_failed_calls_change_nothing(folio):
    folio.buy("ACME", 10, 1_000)
    folio.sell("ACME", 1, 1_500)
    folio.deposit_cash(50_000)
    with pytest.raises(InsufficientShares):
        folio.sell("ACME", 10, 1_500)
    with pytest.raises(InsufficientCash):
        folio.buy("ACME", 1, 10_000_000)
    with pytest.raises(ValueError):
        folio.sell("ACME", 0, 1_500)
    assert folio.get_realized_profit("ACME") == 500
    assert folio.get_cost_basis("ACME") == 9_000


@pytest.mark.parametrize("symbol", ["", 7])
def test_invalid_symbols_are_rejected_by_profit_methods(folio, symbol):
    # None is not here: get_realized_profit(None) means "all symbols".
    with pytest.raises(ValueError):
        folio.get_realized_profit(symbol)
    with pytest.raises(ValueError):
        folio.get_cost_basis(symbol)


def test_cost_basis_rejects_a_missing_symbol(folio):
    with pytest.raises(ValueError):
        folio.get_cost_basis(None)


def test_profit_values_are_ints(folio):
    folio.buy("ACME", 3, 1_000)
    folio.sell("ACME", 1, 1_234)
    assert type(folio.get_realized_profit("ACME")) is int
    assert type(folio.get_realized_profit()) is int
    assert type(folio.get_cost_basis("ACME")) is int
