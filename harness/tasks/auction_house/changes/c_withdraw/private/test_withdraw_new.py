"""Hidden tests for the c_withdraw change (withdrawing bids). Never shown to
the writer or the editor.

Usage (with auction.py importable, e.g. in the sandbox):
    python -m pytest changes/c_withdraw/private/test_withdraw_new.py
"""

import pytest
from auction import AuctionError, AuctionHouse, BidTooLow, VersionConflict


@pytest.fixture
def house():
    h = AuctionHouse()
    h.add_lot("vase", 500)
    h.add_lot("clock", 200)
    h.place_bid("vase", "alice", 500)
    h.place_bid("vase", "bob", 510)
    h.place_bid("vase", "alice", 520)
    h.place_bid("vase", "carol", 530)
    return h


def state(h):
    return {
        lot: (h.get_bids(lot), h.get_highest_bid(lot), h.get_version(lot))
        for lot in h.get_lots()
    }


def test_withdraw_removes_every_bid_of_the_bidder(house):
    house.withdraw_bid("vase", "alice")
    assert house.get_bids("vase") == [("bob", 510), ("carol", 530)]
    assert house.get_highest_bid("vase") == ("carol", 530)


def test_withdraw_of_the_leader_hands_the_lead_back(house):
    house.withdraw_bid("vase", "carol")
    assert house.get_highest_bid("vase") == ("alice", 520)
    assert house.get_leading_lots("alice") == ["vase"]
    assert house.get_leading_lots("carol") == []
    assert house.get_min_bid("vase") == 530


def test_withdraw_of_everyone_returns_to_the_opening_price(house):
    for bidder in ["carol", "alice", "bob"]:
        house.withdraw_bid("vase", bidder)
    assert house.get_bids("vase") == []
    assert house.get_highest_bid("vase") is None
    assert house.get_min_bid("vase") == 500
    with pytest.raises(BidTooLow):
        house.place_bid("vase", "dave", 499)
    house.place_bid("vase", "dave", 500)
    assert house.get_highest_bid("vase") == ("dave", 500)


def test_withdraw_then_bid_again_under_the_normal_rules(house):
    house.withdraw_bid("vase", "carol")
    # alice leads again at 520, so carol needs 530 and alice may not bid
    with pytest.raises(AuctionError):
        house.place_bid("vase", "alice", 600)
    with pytest.raises(BidTooLow):
        house.place_bid("vase", "carol", 529)
    house.place_bid("vase", "carol", 530)
    assert house.get_highest_bid("vase") == ("carol", 530)


def test_withdraw_raises_the_version_by_one(house):
    assert house.get_version("vase") == 5
    house.withdraw_bid("vase", "bob")
    assert house.get_version("vase") == 6
    house.withdraw_bid("vase", "alice", expected_version=6)
    assert house.get_version("vase") == 7
    house.place_bid("vase", "bob", 540, expected_version=7)
    assert house.get_version("vase") == 8


def test_withdraw_only_touches_its_own_lot(house):
    house.place_bid("clock", "alice", 200)
    house.withdraw_bid("vase", "alice")
    assert house.get_bids("clock") == [("alice", 200)]
    assert house.get_version("clock") == 2


def test_withdraw_with_a_stale_version_changes_nothing(house):
    before = state(house)
    with pytest.raises(VersionConflict):
        house.withdraw_bid("vase", "bob", expected_version=4)
    assert state(house) == before


def test_withdraw_twice_raises(house):
    house.withdraw_bid("vase", "bob")
    before = state(house)
    with pytest.raises(AuctionError):
        house.withdraw_bid("vase", "bob")
    assert state(house) == before


def test_withdraw_by_someone_without_bids_raises(house):
    before = state(house)
    with pytest.raises(AuctionError) as info:
        house.withdraw_bid("clock", "alice")
    assert not isinstance(info.value, VersionConflict)
    assert state(house) == before


@pytest.mark.parametrize("bidder", ["", None, 3])
def test_withdraw_invalid_bidders_raise_value_error(house, bidder):
    before = state(house)
    with pytest.raises(ValueError):
        house.withdraw_bid("vase", bidder)
    assert state(house) == before


def test_withdraw_error_order(house):
    with pytest.raises(KeyError):
        house.withdraw_bid("lamp", "", expected_version=0)
    with pytest.raises(KeyError):
        house.withdraw_bid(None, "alice")
    with pytest.raises(ValueError):
        house.withdraw_bid("vase", "", expected_version=0)
    # no bids on the clock and a stale version: the version comes first
    with pytest.raises(VersionConflict):
        house.withdraw_bid("clock", "alice", expected_version=3)
