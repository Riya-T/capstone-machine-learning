Add realized profit to `portfolio.py`, so the investor can see how much
the shares they have sold made or lost.

- Shares are sold first in, first out: a sale takes its shares from the
  oldest purchase of that symbol that still has unsold shares, then from the
  next oldest, and so on. The realized profit of a sale is its proceeds
  minus what the shares it sold cost when they were bought. It can be
  negative.
- Add `Portfolio.get_realized_profit(symbol=None) -> int`. With a symbol it
  returns the realized profit, in cents, summed over every sale of that
  symbol so far; with no symbol, the sum over all symbols. A symbol never
  sold has a realized profit of 0. An invalid symbol raises `ValueError`.
- Add `Portfolio.get_cost_basis(symbol) -> int`: what the shares currently
  held in that symbol cost when they were bought, in cents, so 0 for a
  symbol with no shares held. An invalid symbol raises `ValueError`.
- Deposits change neither value, and failed calls change neither value.

All existing behavior must keep working.
