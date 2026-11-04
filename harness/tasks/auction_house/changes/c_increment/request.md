Make the minimum raise between bids in `auction.py` adjustable, for the
house as a whole and for single lots. Today every later bid must beat the
highest bid by at least 10; that stays the default.

- `AuctionHouse` takes a new keyword argument `min_increment=10`: the
  minimum raise for every lot that does not set its own.
- `add_lot` takes a new keyword argument `min_increment=None`. `None` means
  the lot uses the house's minimum raise; an `int` sets the lot's own.
- A minimum raise (in either place) must be an `int` that is 1 or more;
  anything else raises `ValueError`. Which error `add_lot` raises when the
  minimum raise is invalid and the id was already added is unspecified. In
  every case no lot is added.
- Every bid after the first on a lot must be at least the highest bid plus
  that lot's minimum raise, or `BidTooLow` is raised. The first bid still
  only needs to reach the opening price.
- Add `AuctionHouse.get_min_increment(lot_id) -> int`, which returns the
  minimum raise that applies to the lot.
- Add `AuctionHouse.get_min_bid(lot_id) -> int`, which returns the smallest
  amount the next bid on the lot may be: the opening price while the lot has
  no bids, otherwise the highest bid plus the lot's minimum raise.
- Both raise `KeyError` for a lot that was never added.

All existing behavior must keep working.
