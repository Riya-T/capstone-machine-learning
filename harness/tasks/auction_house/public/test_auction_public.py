"""Public checks for auction.py.

Usage (with auction.py importable, e.g. in the sandbox):
    python -m pytest public/test_auction_public.py
"""

import pytest
from auction import AuctionHouse, BidTooLow


@pytest.fixture
def house():
    h = AuctionHouse()
    h.add_lot("vase", 500)
    h.add_lot("clock", 200)
    return h


def test_a_lot_starts_without_bids(house):
    assert house.get_highest_bid("vase") is None
    assert house.get_bids("vase") == []
    assert house.get_lots() == ["vase", "clock"]


def test_higher_bids_take_the_lead(house):
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 600)
    assert house.get_highest_bid("vase") == ("bob", 600)
    assert house.get_bids("vase") == [("alice", 500), ("bob", 600)]


def test_a_first_bid_below_the_opening_price_raises(house):
    with pytest.raises(BidTooLow):
        house.place_bid("vase", "alice", 499)
    assert house.get_bids("vase") == []


def test_a_bid_that_does_not_beat_the_highest_raises(house):
    house.place_bid("clock", "alice", 300)
    with pytest.raises(BidTooLow):
        house.place_bid("clock", "bob", 305)
    assert house.get_highest_bid("clock") == ("alice", 300)


def test_leading_lots_follow_the_highest_bids(house):
    house.place_bid("vase", "alice", 500)
    house.place_bid("clock", "alice", 200)
    house.place_bid("clock", "bob", 250)
    assert house.get_leading_lots("alice") == ["vase"]
    assert house.get_leading_lots("bob") == ["clock"]
    assert house.get_leading_lots("carol") == []


def test_unknown_lot_raises_key_error(house):
    with pytest.raises(KeyError):
        house.get_bids("lamp")
