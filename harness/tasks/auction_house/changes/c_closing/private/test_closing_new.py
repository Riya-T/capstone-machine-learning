"""Hidden tests for the c_closing change (closed lots). Never shown to the
writer or the editor.

Usage (with auction.py importable, e.g. in the sandbox):
    python -m pytest changes/c_closing/private/test_closing_new.py
"""

import pytest
from auction import AuctionError, AuctionHouse, BidTooLow, LotClosed


@pytest.fixture
def house():
    h = AuctionHouse()
    h.add_lot("vase", 500)
    h.add_lot("clock", 200)
    h.add_lot("rug", 100)
    h.place_bid("vase", "alice", 500)
    h.place_bid("vase", "bob", 550)
    h.place_bid("clock", "alice", 200)
    return h


def state(h):
    return {
        lot: (h.get_bids(lot), h.get_highest_bid(lot), h.is_closed(lot))
        for lot in h.get_lots()
    }


def test_closing_new_lots_are_open(house):
    assert [house.is_closed(lot) for lot in house.get_lots()] == [False, False, False]
    assert house.get_open_lots() == ["vase", "clock", "rug"]


def test_closing_returns_the_highest_bidder(house):
    assert house.close_lot("vase") == "bob"
    assert house.close_lot("clock") == "alice"
    assert house.close_lot("rug") is None
    assert house.get_winner("vase") == "bob"
    assert house.get_winner("clock") == "alice"
    assert house.get_winner("rug") is None


def test_closing_keeps_the_order_of_open_lots(house):
    house.close_lot("clock")
    assert house.get_open_lots() == ["vase", "rug"]
    house.close_lot("vase")
    assert house.get_open_lots() == ["rug"]
    assert house.get_lots() == ["vase", "clock", "rug"]


def test_closing_twice_raises_lot_closed(house):
    house.close_lot("vase")
    before = state(house)
    with pytest.raises(LotClosed):
        house.close_lot("vase")
    assert state(house) == before
    assert house.get_winner("vase") == "bob"


def test_closing_refuses_every_later_bid(house):
    house.close_lot("vase")
    before = state(house)
    for bidder, amount in [("carol", 10_000), ("alice", 560), ("bob", 999)]:
        with pytest.raises(LotClosed):
            house.place_bid("vase", bidder, amount)
    assert state(house) == before


def test_closing_a_lot_leaves_the_others_open_for_bids(house):
    house.close_lot("vase")
    house.place_bid("clock", "bob", 210)
    house.place_bid("rug", "carol", 100)
    assert house.get_highest_bid("clock") == ("bob", 210)
    assert house.get_highest_bid("rug") == ("carol", 100)


def test_closing_leaves_bids_readable(house):
    house.close_lot("vase")
    assert house.get_bids("vase") == [("alice", 500), ("bob", 550)]
    assert house.get_leading_lots("bob") == ["vase"]
    assert house.get_leading_lots("alice") == ["clock"]


def test_closing_get_winner_of_an_open_lot_raises(house):
    with pytest.raises(AuctionError) as info:
        house.get_winner("vase")
    assert not isinstance(info.value, LotClosed)
    with pytest.raises(AuctionError):
        house.get_winner("rug")


@pytest.mark.parametrize("method", ["close_lot", "is_closed", "get_winner"])
def test_closing_unknown_lots_raise_key_error(house, method):
    house.close_lot("vase")
    before = state(house)
    with pytest.raises(KeyError):
        getattr(house, method)("lamp")
    with pytest.raises(KeyError):
        getattr(house, method)(None)
    assert state(house) == before


def test_closing_error_order_for_bids(house):
    house.close_lot("vase")
    with pytest.raises(ValueError):
        house.place_bid("vase", "", 600)
    with pytest.raises(ValueError):
        house.place_bid("vase", "carol", -1)
    # bob leads the closed lot: closed is reported before the leader rule
    with pytest.raises(LotClosed):
        house.place_bid("vase", "bob", 900)
    # and before a bid that is too low
    with pytest.raises(LotClosed):
        house.place_bid("vase", "carol", 1)


def test_lot_closed_is_an_auction_error():
    assert issubclass(LotClosed, AuctionError)
    assert not issubclass(LotClosed, BidTooLow)
