# Auction house

Write a module `auction.py` that runs an auction house: lots are put up for
sale, and bidders place ever higher bids on them.

## Interface

```python
class AuctionError(Exception): ...


class BidTooLow(AuctionError): ...


class AuctionHouse:
    def __init__(self): ...
    def add_lot(self, lot_id: str, opening_price: int) -> None: ...
    def place_bid(self, lot_id: str, bidder: str, amount: int) -> None: ...
    def get_highest_bid(self, lot_id: str) -> tuple[str, int] | None: ...
    def get_bids(self, lot_id: str) -> list[tuple[str, int]]: ...
    def get_leading_lots(self, bidder: str) -> list[str]: ...
    def get_lots(self) -> list[str]: ...
```

All prices and bids are whole cents, as `int`.

## Lots

- `add_lot(lot_id, opening_price)` puts a lot up for sale with no bids. The
  id must be a non-empty string and the opening price an `int` greater than
  0; otherwise `ValueError` is raised. Adding an id that was already added
  raises `AuctionError`. `ValueError` is checked first.
- `get_lots()` returns the ids of all lots, in the order they were added.
- Every other method that takes a `lot_id` raises `KeyError` when given an
  id that was never added, including values that are not strings at all,
  such as `None` or `1`.

## Bidding

`place_bid(lot_id, bidder, amount)` records a bid by `bidder` on the lot.

- The bidder must be a non-empty string (so `""` and `None` are invalid),
  and the amount an `int` greater than 0; otherwise `ValueError` is raised.
- Each lot has a minimum bid. While the lot has no bids, the minimum is its
  opening price. Once it has bids, the minimum is the current highest bid
  plus 10. For example, if the highest bid is 250, a bid of 260 is accepted
  and a bid of 259 is not.
- A bid below the minimum raises `BidTooLow`. Any other valid bid, including
  the first bid on a lot, is recorded and becomes the lot's highest bid.
- The bidder who holds the highest bid on a lot may not bid on that lot
  again until someone else outbids them; trying raises `AuctionError` (not
  `BidTooLow`).

When a call has several problems, the first of these is raised:

1. `KeyError` for a lot that was never added;
2. `ValueError` for an invalid bidder, then for an invalid amount;
3. `AuctionError` for a bidder who already holds the highest bid;
4. `BidTooLow`.

## Reading the bids

- `get_highest_bid(lot_id)` returns the highest bid on the lot as a
  `(bidder, amount)` tuple, or `None` if the lot has no bids yet.
- `get_bids(lot_id)` returns every accepted bid on the lot, oldest first, as
  `(bidder, amount)` tuples.
- `get_leading_lots(bidder)` returns the ids of the lots on which `bidder`
  currently holds the highest bid, in the order the lots were added. A bidder
  who has never bid gets an empty list.

A failed call has no effect: if a method raises, every lot and every bid is
unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids or bidders that are not strings passed to `add_lot` or
`get_leading_lots`, bidders passed to `place_bid` that are neither strings
nor `None`, `bool` prices or amounts, what happens if a returned
list is changed, the text of error messages, saving the auction house to a
file, and use from several threads.
