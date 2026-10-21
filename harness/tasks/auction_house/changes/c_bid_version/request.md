Bidders in `auction.py` often look at a lot and then bid a moment later,
by which time someone else may have bid. Give each lot a version number so a
bid can say which state of the lot it was based on.

- Add `class VersionConflict(AuctionError)` to `auction.py`.
- Add `AuctionHouse.get_version(lot_id) -> int`. A new lot has version 1.
  The version goes up by 1 every time the lot's list of bids changes, which
  today means every accepted bid. Calls that fail, and calls that only read,
  leave it unchanged. It raises `KeyError` for a lot that was never added.
- `place_bid` takes a new keyword argument `expected_version=None`. When it
  is `None` the bid works as before. Otherwise, if it is not equal to the
  lot's current version, `VersionConflict` is raised and nothing changes.
- `VersionConflict` is checked after the `KeyError` and every `ValueError`
  check, and before every other error `place_bid` can raise.
- Each lot has its own version: a bid on one lot does not change the
  version of any other.

All existing behavior must keep working.
