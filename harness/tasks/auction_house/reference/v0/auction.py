"""Auction house: lots for sale and the bids placed on them.

Correct solution for auction_house before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from auction import AuctionHouse
    house = AuctionHouse()
    house.add_lot("vase", 500)
    house.place_bid("vase", "alice", 500)
"""

MIN_INCREMENT = 10


class AuctionError(Exception):
    pass


class BidTooLow(AuctionError):
    pass


def check_positive_int(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


class AuctionHouse:
    def __init__(self):
        self._opening = {}  # lot id -> opening price, in the order added
        self._bids = {}  # lot id -> list of (bidder, amount), oldest first

    def add_lot(self, lot_id, opening_price):
        check_name(lot_id, "lot_id")
        check_positive_int(opening_price, "opening_price")
        if lot_id in self._opening:
            raise AuctionError(f"lot {lot_id!r} already exists")
        self._opening[lot_id] = opening_price
        self._bids[lot_id] = []

    def place_bid(self, lot_id, bidder, amount):
        self._require(lot_id)
        check_name(bidder, "bidder")
        check_positive_int(amount, "amount")
        highest = self.get_highest_bid(lot_id)
        if highest is not None and highest[0] == bidder:
            raise AuctionError(f"{bidder!r} already holds the highest bid")
        if amount < self._min_bid(lot_id):
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

    def _require(self, lot_id):
        # Non-str ids are never stored, so they count as "never added" too.
        if not isinstance(lot_id, str) or lot_id not in self._opening:
            raise KeyError(lot_id)

    def _min_bid(self, lot_id):
        bids = self._bids[lot_id]
        if not bids:
            return self._opening[lot_id]
        return bids[-1][1] + MIN_INCREMENT
