# Stock portfolio

Write a module `portfolio.py` that keeps track of one investor's portfolio:
the cash available, the shares held in each stock, and every trade made.

## Interface

```python
class PortfolioError(Exception): ...


class InsufficientCash(PortfolioError): ...


class InsufficientShares(PortfolioError): ...


class Portfolio:
    def __init__(self): ...
    def deposit_cash(self, amount: int) -> None: ...
    def buy(self, symbol: str, shares: int, price: int) -> None: ...
    def sell(self, symbol: str, shares: int, price: int) -> None: ...
    def get_cash(self) -> int: ...
    def get_shares(self, symbol: str) -> int: ...
    def get_holdings(self) -> list[str]: ...
    def get_trades(self) -> list[tuple[str, str, int, int]]: ...
```

All cash amounts and prices are whole cents, as `int`. A price is the price
of one share.

## Cash

- A new portfolio has 0 cash and holds no shares.
- `deposit_cash(amount)` adds the amount to the cash. The amount must be an
  `int` greater than 0, or `ValueError` is raised.
- `get_cash()` returns the cash available.

## Trading

- A symbol must be a non-empty string, or `ValueError` is raised. This
  applies to every method that takes a symbol.
- The number of shares and the price must each be an `int` greater than 0,
  or `ValueError` is raised.
- `buy(symbol, shares, price)` takes `shares * price` out of the cash and
  adds the shares to the holding in that symbol. Buying more than the cash
  can pay for raises `InsufficientCash`.
- `sell(symbol, shares, price)` takes the shares out of the holding and adds
  `shares * price` to the cash. Selling more shares than are held raises
  `InsufficientShares`; a symbol never bought holds 0 shares.
- `get_shares(symbol)` returns the number of shares held in that symbol, 0
  for a symbol never bought.
- `get_holdings()` returns the symbols with more than 0 shares, in the order
  they were first bought. A symbol sold down to 0 shares is not listed.

When a call has several problems, the first of these is raised:

1. `ValueError` for an invalid symbol;
2. `ValueError` for an invalid number of shares;
3. `ValueError` for an invalid price;
4. `InsufficientCash` or `InsufficientShares`.

## Trades

`get_trades()` returns every trade made, oldest first, as
`(kind, symbol, shares, price)` tuples where `kind` is `"buy"` or `"sell"`.
Deposits are not trades.

A failed call has no effect: if a method raises, the cash, every holding and
the list of trades are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` amounts, shares or prices, where a symbol sold down to 0 and
bought again appears in `get_holdings()`, what happens if a returned list is
changed, the text of error messages, saving the portfolio to a file, and use
from several threads.
