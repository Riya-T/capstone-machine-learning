"""Hidden tests for the initial auction_house spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with auction.py importable, e.g. in the sandbox):
    python -m pytest private/test_auction_initial.py
"""

import pytest
from auction import AuctionError, AuctionHouse, BidTooLow

BAD_NUMBERS = [0, -5, 1.5, "100", None]
BAD_NAMES = ["", None]


@pytest.fixture
def house():
    h = AuctionHouse()
    h.add_lot("vase", 500)
    h.add_lot("clock", 200)
    return h


def state(h):
    """Every lot's bids, to check that a failed call changed nothing."""
    return {lot: (h.get_bids(lot), h.get_highest_bid(lot)) for lot in h.get_lots()}


# --- lots -------------------------------------------------------------------


def test_lots_are_listed_in_the_order_added():
    h = AuctionHouse()
    for name in ["rug", "lamp", "desk"]:
        h.add_lot(name, 100)
    assert h.get_lots() == ["rug", "lamp", "desk"]


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_lot_ids_are_rejected(bad_id):
    h = AuctionHouse()
    with pytest.raises(ValueError):
        h.add_lot(bad_id, 100)
    assert h.get_lots() == []


@pytest.mark.parametrize("price", BAD_NUMBERS)
def test_invalid_opening_prices_are_rejected(price):
    h = AuctionHouse()
    with pytest.raises(ValueError):
        h.add_lot("rug", price)
    assert h.get_lots() == []


def test_adding_a_lot_twice_is_rejected(house):
    house.place_bid("vase", "alice", 500)
    before = state(house)
    with pytest.raises(AuctionError):
        house.add_lot("vase", 50)
    assert state(house) == before
    assert house.get_lots() == ["vase", "clock"]


def test_a_bad_price_is_reported_before_a_duplicate_id(house):
    with pytest.raises(ValueError):
        house.add_lot("vase", 0)


@pytest.mark.parametrize(
    "call",
    [
        lambda h: h.place_bid("lamp", "alice", 500),
        lambda h: h.get_highest_bid("lamp"),
        lambda h: h.get_bids("lamp"),
        lambda h: h.get_bids(None),
        lambda h: h.get_highest_bid(1),
    ],
)
def test_lots_that_were_never_added_raise_key_error(house, call):
    house.place_bid("vase", "alice", 500)
    before = state(house)
    with pytest.raises(KeyError):
        call(house)
    assert state(house) == before


# --- bidding ----------------------------------------------------------------


def test_the_first_bid_may_equal_the_opening_price(house):
    house.place_bid("vase", "alice", 500)
    assert house.get_highest_bid("vase") == ("alice", 500)


def test_the_first_bid_may_exceed_the_opening_price(house):
    house.place_bid("clock", "alice", 999)
    assert house.get_highest_bid("clock") == ("alice", 999)


def test_a_raise_of_exactly_ten_is_accepted(house):
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 510)
    house.place_bid("vase", "alice", 520)
    assert house.get_bids("vase") == [("alice", 500), ("bob", 510), ("alice", 520)]


def test_a_raise_of_nine_is_too_low(house):
    house.place_bid("vase", "alice", 500)
    before = state(house)
    with pytest.raises(BidTooLow):
        house.place_bid("vase", "bob", 509)
    assert state(house) == before


def test_a_bid_below_the_opening_price_changes_nothing(house):
    before = state(house)
    with pytest.raises(BidTooLow):
        house.place_bid("clock", "alice", 199)
    assert state(house) == before


def test_the_leader_may_not_bid_again(house):
    house.place_bid("vase", "alice", 500)
    before = state(house)
    with pytest.raises(AuctionError) as info:
        house.place_bid("vase", "alice", 900)
    assert not isinstance(info.value, BidTooLow)
    assert state(house) == before


def test_an_outbid_bidder_may_bid_again(house):
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 550)
    house.place_bid("vase", "alice", 560)
    assert house.get_highest_bid("vase") == ("alice", 560)


def test_lots_are_bid_on_independently(house):
    house.place_bid("vase", "alice", 800)
    house.place_bid("clock", "alice", 200)
    house.place_bid("clock", "bob", 210)
    assert house.get_highest_bid("vase") == ("alice", 800)
    assert house.get_highest_bid("clock") == ("bob", 210)


@pytest.mark.parametrize("bidder", BAD_NAMES)
def test_invalid_bidders_are_rejected(house, bidder):
    before = state(house)
    with pytest.raises(ValueError):
        house.place_bid("vase", bidder, 500)
    assert state(house) == before


@pytest.mark.parametrize("amount", BAD_NUMBERS)
def test_invalid_amounts_are_rejected(house, amount):
    house.place_bid("vase", "alice", 500)
    before = state(house)
    with pytest.raises(ValueError):
        house.place_bid("vase", "bob", amount)
    assert state(house) == before


def test_error_order_for_bids(house):
    house.place_bid("vase", "alice", 500)
    with pytest.raises(KeyError):
        house.place_bid("lamp", "", -1)
    with pytest.raises(ValueError):
        house.place_bid("vase", "", -1)
    # alice leads and 1 is too low: the leader rule comes first.
    with pytest.raises(AuctionError) as info:
        house.place_bid("vase", "alice", 1)
    assert not isinstance(info.value, BidTooLow)
    # an invalid amount from the leader is a ValueError
    with pytest.raises(ValueError):
        house.place_bid("vase", "alice", 0)


# --- reading the bids --------------------------------------------------------


def test_leading_lots_are_in_the_order_lots_were_added():
    h = AuctionHouse()
    for name in ["rug", "lamp", "desk"]:
        h.add_lot(name, 100)
    h.place_bid("desk", "alice", 100)
    h.place_bid("rug", "alice", 100)
    h.place_bid("lamp", "bob", 100)
    assert h.get_leading_lots("alice") == ["rug", "desk"]
    h.place_bid("rug", "bob", 150)
    assert h.get_leading_lots("alice") == ["desk"]
    assert h.get_leading_lots("bob") == ["rug", "lamp"]


def test_an_outbid_bidder_leads_nothing(house):
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 510)
    assert house.get_leading_lots("alice") == []


def test_bid_too_low_is_an_auction_error():
    assert issubclass(BidTooLow, AuctionError)


def test_houses_do_not_share_lots():
    first, second = AuctionHouse(), AuctionHouse()
    first.add_lot("vase", 500)
    first.place_bid("vase", "alice", 500)
    assert second.get_lots() == []
    second.add_lot("vase", 100)
    assert second.get_bids("vase") == []
    assert second.get_leading_lots("alice") == []
