"""Stock portfolio whose symbols can be grouped into sectors.

Correct solution for stock_portfolio after c_sectors.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from portfolio import Portfolio
    folio = Portfolio()
    folio.deposit_cash(100_000)
    folio.buy("ACME", 10, 2_500)
    folio.set_sector("ACME", "industrials")
    folio.get_sector_holdings("industrials")
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
        self._sectors = {}  # symbol -> sector name
        self._sector_order = []  # sector names in the order first used

    def deposit_cash(self, amount):
        check_positive(amount, "amount")
        self._cash += amount

    def buy(self, symbol, shares, price):
        check_symbol(symbol)
        check_positive(shares, "shares")
        check_positive(price, "price")
        cost = shares * price
        if cost > self._cash:
            raise InsufficientCash(f"buying {shares} {symbol} costs {cost}, cash is {self._cash}")
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

    def set_sector(self, symbol, sector):
        check_symbol(symbol)
        if not isinstance(sector, str) or not sector:
            raise ValueError(f"sector must be a non-empty str, got {sector!r}")
        self._sectors[symbol] = sector
        if sector not in self._sector_order:
            self._sector_order.append(sector)

    def get_sector(self, symbol):
        check_symbol(symbol)
        if symbol not in self._sectors:
            raise KeyError(symbol)
        return self._sectors[symbol]

    def get_sectors(self):
        in_use = set(self._sectors.values())
        return [sector for sector in self._sector_order if sector in in_use]

    def get_sector_holdings(self, sector):
        if sector not in self.get_sectors():
            raise KeyError(sector)
        return [symbol for symbol in self.get_holdings() if self._sectors.get(symbol) == sector]
