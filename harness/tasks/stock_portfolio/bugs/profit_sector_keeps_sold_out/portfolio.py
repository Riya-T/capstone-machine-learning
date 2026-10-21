"""Stock portfolio with sectors and first-in, first-out realized profit.

Planted bug (after c_sectors and c_profit): realized profit was added
correctly, but get_sector_holdings now lists every symbol in the sector that
was ever bought, including ones sold down to 0 shares.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from portfolio import Portfolio
    folio = Portfolio()
    folio.deposit_cash(100_000)
    folio.buy("ACME", 10, 2_500)
    folio.sell("ACME", 4, 3_000)
    folio.get_realized_profit("ACME")
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
        self._lots = {}  # symbol -> list of [shares, price] not yet sold, oldest first
        self._trades = []  # (kind, symbol, shares, price), oldest first
        self._realized = {}  # symbol -> realized profit in cents
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
        self._lots.setdefault(symbol, []).append([shares, price])
        self._trades.append(("buy", symbol, shares, price))

    def sell(self, symbol, shares, price):
        check_symbol(symbol)
        check_positive(shares, "shares")
        check_positive(price, "price")
        held = self.get_shares(symbol)
        if shares > held:
            raise InsufficientShares(f"only {held} {symbol} held, cannot sell {shares}")
        self._cash += shares * price
        self._realized[symbol] = self._realized.get(symbol, 0) + self._take_lots(
            symbol, shares, price
        )
        self._trades.append(("sell", symbol, shares, price))

    def get_cash(self):
        return self._cash

    def get_shares(self, symbol):
        check_symbol(symbol)
        return sum(shares for shares, _ in self._lots.get(symbol, []))

    def get_holdings(self):
        return [symbol for symbol in self._lots if self.get_shares(symbol) > 0]

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
        return [symbol for symbol in self._lots if self._sectors.get(symbol) == sector]

    def get_realized_profit(self, symbol=None):
        if symbol is None:
            return sum(self._realized.values())
        check_symbol(symbol)
        return self._realized.get(symbol, 0)

    def get_cost_basis(self, symbol):
        check_symbol(symbol)
        return sum(shares * price for shares, price in self._lots.get(symbol, []))

    def _take_lots(self, symbol, shares, sale_price):
        """Remove `shares` from the oldest lots; return the profit on them."""
        lots = self._lots[symbol]
        profit = 0
        while shares > 0:
            lot = lots[0]
            taken = min(shares, lot[0])
            profit += taken * (sale_price - lot[1])
            lot[0] -= taken
            shares -= taken
            if lot[0] == 0:
                lots.pop(0)
        return profit
