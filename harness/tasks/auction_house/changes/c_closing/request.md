Let lots in `auction.py` be closed when their sale ends, so that the
highest bidder wins and no more bids come in.

- Add `class LotClosed(AuctionError)` to `auction.py`.
- Add `AuctionHouse.close_lot(lot_id) -> str | None`. It closes the lot and
  returns the winner: the bidder holding the highest bid, or `None` if the
  lot has no bids. Closing a lot that is already closed raises `LotClosed`.
- Add `AuctionHouse.is_closed(lot_id) -> bool`. New lots are open.
- Add `AuctionHouse.get_winner(lot_id) -> str | None`, which returns the
  winner of a closed lot (`None` if it closed without bids). For a lot that
  is still open it raises `AuctionError`.
- Add `AuctionHouse.get_open_lots() -> list[str]`: the ids of the lots that
  are not closed, in the order they were added. `get_lots` still lists all
  lots.
- A bid on a closed lot raises `LotClosed` and changes nothing. In
  `place_bid` this is checked after the `KeyError` and every `ValueError`
  check, and before every other error.
- `get_highest_bid`, `get_bids` and `get_leading_lots` keep working for
  closed lots: their bids stay where they are.
- `close_lot`, `is_closed` and `get_winner` raise `KeyError` for a lot that
  was never added, before any other error.

All existing behavior must keep working.
