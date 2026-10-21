"""Auction house with closed lots and an adjustable minimum raise.

Planted bug (after c_closing and c_increment): the minimum raise works, but
closing a lot that is already closed no longer raises LotClosed.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from auction import AuctionHouse
    house = AuctionHouse(min_increment=25)
    house.add_lot("vase", 500, min_increment=5)
    house.place_bid("vase", "alice", 500)
"""


class AuctionError(Exception):
    pass


class BidTooLow(AuctionError):
    pass


class LotClosed(AuctionError):
    pass


def check_positive_int(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


class AuctionHouse:
    def __init__(self, min_increment=10):
        check_positive_int(min_increment, "min_increment")
        self._default_increment = min_increment
        self._opening = {}  # lot id -> opening price, in the order added
        self._increments = {}  # lot id -> minimum raise for that lot
        self._bids = {}  # lot id -> list of (bidder, amount), oldest first
        self._closed = set()  # ids of closed lots

    def add_lot(self, lot_id, opening_price, min_increment=None):
        check_name(lot_id, "lot_id")
        check_positive_int(opening_price, "opening_price")
        if min_increment is None:
            min_increment = self._default_increment
        check_positive_int(min_increment, "min_increment")
        if lot_id in self._opening:
            raise AuctionError(f"lot {lot_id!r} already exists")
        self._opening[lot_id] = opening_price
        self._increments[lot_id] = min_increment
        self._bids[lot_id] = []

    def place_bid(self, lot_id, bidder, amount):
        self._require(lot_id)
        check_name(bidder, "bidder")
        check_positive_int(amount, "amount")
        self._require_open(lot_id)
        highest = self.get_highest_bid(lot_id)
        if highest is not None and highest[0] == bidder:
            raise AuctionError(f"{bidder!r} already holds the highest bid")
        if amount < self.get_min_bid(lot_id):
            raise BidTooLow(f"bid of {amount} on {lot_id!r} is too low")
        self._bids[lot_id].append((bidder, amount))

    def get_highest_bid(self, lot_id):
        self._require(lot_id)
        bids = self._bids[lot_id]
        return bids[-1] if bids else None

    def get_bids(self, lot_id):
        self._require(lot_id)
        return list(self._bids[lot_id])

    def get_leading_lots(self, bidder):
        return [
            lot_id
            for lot_id, bids in self._bids.items()
            if bids and bids[-1][0] == bidder
        ]

    def get_lots(self):
        return list(self._opening)

    def get_min_increment(self, lot_id):
        self._require(lot_id)
        return self._increments[lot_id]

    def get_min_bid(self, lot_id):
        self._require(lot_id)
        bids = self._bids[lot_id]
        if not bids:
            return self._opening[lot_id]
        return bids[-1][1] + self._increments[lot_id]

    def close_lot(self, lot_id):
        self._require(lot_id)
        self._closed.add(lot_id)
        highest = self.get_highest_bid(lot_id)
        return highest[0] if highest else None

    def is_closed(self, lot_id):
        self._require(lot_id)
        return lot_id in self._closed

    def get_winner(self, lot_id):
        self._require(lot_id)
        if lot_id not in self._closed:
            raise AuctionError(f"lot {lot_id!r} is still open")
        highest = self.get_highest_bid(lot_id)
        return highest[0] if highest else None

    def get_open_lots(self):
        return [lot_id for lot_id in self._opening if lot_id not in self._closed]

    def _require(self, lot_id):
        # Non-str ids are never stored, so they count as "never added" too.
        if not isinstance(lot_id, str) or lot_id not in self._opening:
            raise KeyError(lot_id)

    def _require_open(self, lot_id):
        if lot_id in self._closed:
            raise LotClosed(f"lot {lot_id!r} is closed")
