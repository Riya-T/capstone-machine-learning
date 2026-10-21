"""Stock portfolio: a cash balance, the shares held per symbol, and a record
of every trade.

Planted bug (initial version): `buy` checks the cash before the price is
validated, so a bad price with too little cash reports InsufficientCash
instead of ValueError. The public checks always have plenty of cash when
they pass a bad price, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from portfolio import Portfolio
    folio = Portfolio()
    folio.deposit_cash(100_000)
    folio.buy("ACME", 10, 2_500)
    folio.sell("ACME", 4, 3_000)
"""


class PortfolioError(Exception):
    pass


class InsufficientCash(PortfolioError):
    pass


class InsufficientShares(PortfolioError):
    pass


def check_symbol(symbol):
    if not isinstance(symbol, str) or not symbol:
        raise ValueError(f"symbol must be a non-empty str, got {symbol!r}")


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


class Portfolio:
    def __init__(self):
        self._cash = 0  # cents available
        self._shares = {}  # symbol -> shares held, in the order symbols were first bought
        self._trades = []  # (kind, symbol, shares, price), oldest first

    def deposit_cash(self, amount):
        check_positive(amount, "amount")
        self._cash += amount

    def buy(self, symbol, shares, price):
        check_symbol(symbol)
        check_positive(shares, "shares")
        cost = shares * price
        if cost > self._cash:
            raise InsufficientCash(f"buying {shares} {symbol} costs {cost}, cash is {self._cash}")
        check_positive(price, "price")
        self._cash -= cost
        self._shares[symbol] = self._shares.get(symbol, 0) + shares
        self._trades.append(("buy", symbol, shares, price))

    def sell(self, symbol, shares, price):
        check_symbol(symbol)
        check_positive(shares, "shares")
        check_positive(price, "price")
        held = self._shares.get(symbol, 0)
        if shares > held:
            raise InsufficientShares(f"only {held} {symbol} held, cannot sell {shares}")
        self._cash += shares * price
        self._shares[symbol] = held - shares
        self._trades.append(("sell", symbol, shares, price))

    def get_cash(self):
        return self._cash

    def get_shares(self, symbol):
        check_symbol(symbol)
        return self._shares.get(symbol, 0)

    def get_holdings(self):
        return [symbol for symbol, held in self._shares.items() if held > 0]

    def get_trades(self):
        return list(self._trades)
