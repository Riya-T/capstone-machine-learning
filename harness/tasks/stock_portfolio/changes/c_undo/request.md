Let the most recent trade in `portfolio.py` be cancelled, for example when
it was entered by mistake.

- Add `Portfolio.cancel_last_trade() -> tuple[str, str, int, int]`. It
  reverses the most recent trade that has not been cancelled yet and
  returns that trade's `(kind, symbol, shares, price)` tuple.
- After the call, the cash, the shares held in every symbol, `get_holdings()`
  and `get_trades()` are exactly as they were before that trade was made:
  cancelling a buy gives the cash back and removes the shares, cancelling a
  sell takes the proceeds back and returns the shares. The cancelled trade
  no longer appears in `get_trades()`.
- Calling it again cancels the trade before that, and so on. When there is
  no trade left to cancel it raises `PortfolioError` and nothing changes.
- Deposits are not trades and are never cancelled: cash deposited after the
  trade stays.

All existing behavior must keep working.
