Let a bidder in `auction.py` take back their bids on a lot, for example
after bidding by mistake.

- Add `AuctionHouse.withdraw_bid(lot_id, bidder, expected_version=None)`.
  It removes every bid that `bidder` has placed on the lot so far. The other
  bids stay, in their order.
- After a withdrawal, the highest remaining bid is the highest bid again:
  `get_highest_bid`, `get_bids`, `get_leading_lots` and `get_min_bid` all
  behave as if the removed bids had never been placed. If no bids remain,
  the lot is back to having no bids, and the next bid only needs to reach
  the opening price.
- A bidder who withdrew may bid on the lot again later, under the normal
  rules.
- A withdrawal changes the lot's list of bids, so a successful one raises
  the lot's version by 1. `expected_version` works as it does for
  `place_bid`: when it is given and is not equal to the lot's current
  version, `VersionConflict` is raised.
- `withdraw_bid` raises:
  - `KeyError` for an unknown lot;
  - `ValueError` if `bidder` is not a non-empty string;
  - `VersionConflict` as described above;
  - `AuctionError` if `bidder` is valid but has no bids on the lot
    (including a bidder whose bids were already withdrawn).

  Which of these is raised when a call has several problems is
  unspecified.
- A failed withdrawal changes nothing, including the version.

All existing behavior must keep working.
