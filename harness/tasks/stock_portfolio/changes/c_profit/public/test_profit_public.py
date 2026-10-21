"""Public checks for the c_profit change (realized profit). Shown to the
editor, never to the writer.

Usage (with portfolio.py importable, e.g. in the sandbox):
    python -m pytest changes/c_profit/public/test_profit_public.py
"""

from portfolio import Portfolio


def test_profit_is_proceeds_minus_what_the_shares_cost():
    pf = Portfolio()
    pf.deposit_cash(100_000)
    pf.buy("ACME", 10, 2_000)
    pf.sell("ACME", 4, 2_500)
    assert pf.get_realized_profit("ACME") == 2_000
    assert pf.get_realized_profit() == 2_000
    assert pf.get_cost_basis("ACME") == 12_000


def test_shares_are_sold_oldest_purchase_first():
    pf = Portfolio()
    pf.deposit_cash(100_000)
    pf.buy("ACME", 5, 1_000)
    pf.buy("ACME", 5, 3_000)
    pf.sell("ACME", 6, 2_000)
    # 5 shares bought at 1_000 and 1 share bought at 3_000.
    assert pf.get_realized_profit("ACME") == 5_000 - 1_000
    assert pf.get_cost_basis("ACME") == 12_000


def test_nothing_sold_means_no_profit():
    pf = Portfolio()
    pf.deposit_cash(10_000)
    pf.buy("ACME", 1, 1_000)
    assert pf.get_realized_profit() == 0
    assert pf.get_realized_profit("BOLT") == 0
    assert pf.get_cost_basis("BOLT") == 0
