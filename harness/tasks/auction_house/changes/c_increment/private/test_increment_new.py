"""Hidden tests for the c_increment change (adjustable minimum raise). Never
shown to the writer or the editor.

Usage (with auction.py importable, e.g. in the sandbox):
    python -m pytest changes/c_increment/private/test_increment_new.py
"""

import pytest
from auction import AuctionError, AuctionHouse, BidTooLow

BAD_INCREMENTS = [0, -1, 2.5, "5", True]


def state(h):
    return {lot: (h.get_bids(lot), h.get_min_increment(lot)) for lot in h.get_lots()}


def test_increment_default_is_ten():
    house = AuctionHouse()
    house.add_lot("vase", 500)
    assert house.get_min_increment("vase") == 10
    house.place_bid("vase", "alice", 500)
    assert house.get_min_bid("vase") == 510


def test_increment_min_bid_is_the_opening_price_without_bids():
    house = AuctionHouse(min_increment=75)
    house.add_lot("vase", 500)
    assert house.get_min_bid("vase") == 500
    with pytest.raises(BidTooLow):
        house.place_bid("vase", "alice", 499)
    house.place_bid("vase", "alice", 500)


def test_increment_house_value_applies_to_every_lot():
    house = AuctionHouse(min_increment=25)
    house.add_lot("vase", 500)
    house.add_lot("clock", 200)
    house.place_bid("clock", "alice", 200)
    with pytest.raises(BidTooLow):
        house.place_bid("clock", "bob", 224)
    house.place_bid("clock", "bob", 225)
    assert house.get_min_increment("vase") == 25
    assert house.get_min_bid("clock") == 250


def test_increment_lot_value_overrides_the_house_value():
    house = AuctionHouse(min_increment=100)
    house.add_lot("vase", 500, min_increment=5)
    house.add_lot("clock", 200, min_increment=None)
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 505)
    house.place_bid("clock", "alice", 200)
    with pytest.raises(BidTooLow):
        house.place_bid("clock", "bob", 299)
    assert house.get_min_increment("vase") == 5
    assert house.get_min_increment("clock") == 100
    assert house.get_min_bid("vase") == 510
    assert house.get_min_bid("clock") == 300


def test_increment_of_one_allows_any_higher_bid():
    house = AuctionHouse(min_increment=1)
    house.add_lot("vase", 500)
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 501)
    assert house.get_highest_bid("vase") == ("bob", 501)


def test_increment_min_bid_follows_the_highest_bid():
    house = AuctionHouse()
    house.add_lot("vase", 500, min_increment=20)
    house.place_bid("vase", "alice", 600)
    house.place_bid("vase", "bob", 700)
    assert house.get_min_bid("vase") == 720


@pytest.mark.parametrize("bad", BAD_INCREMENTS)
def test_increment_invalid_house_values_are_rejected(bad):
    with pytest.raises(ValueError):
        AuctionHouse(min_increment=bad)


@pytest.mark.parametrize("bad", BAD_INCREMENTS)
def test_increment_invalid_lot_values_are_rejected(bad):
    house = AuctionHouse()
    house.add_lot("clock", 200)
    with pytest.raises(ValueError):
        house.add_lot("vase", 500, min_increment=bad)
    assert house.get_lots() == ["clock"]


def test_increment_add_lot_error_order():
    house = AuctionHouse()
    house.add_lot("vase", 500)
    with pytest.raises(ValueError):
        house.add_lot("", 500, min_increment=0)
    with pytest.raises(ValueError):
        house.add_lot("clock", 0, min_increment=0)
    # a bad minimum raise is reported before the duplicate id
    with pytest.raises(ValueError):
        house.add_lot("vase", 500, min_increment=0)
    before = state(house)
    with pytest.raises(AuctionError):
        house.add_lot("vase", 500, min_increment=3)
    assert state(house) == before


@pytest.mark.parametrize("method", ["get_min_increment", "get_min_bid"])
def test_increment_getters_raise_key_error_for_unknown_lots(method):
    house = AuctionHouse()
    with pytest.raises(KeyError):
        getattr(house, method)("vase")


def test_increment_leader_rule_still_comes_first():
    house = AuctionHouse(min_increment=50)
    house.add_lot("vase", 500)
    house.place_bid("vase", "alice", 500)
    with pytest.raises(AuctionError) as info:
        house.place_bid("vase", "alice", 520)
    assert not isinstance(info.value, BidTooLow)
