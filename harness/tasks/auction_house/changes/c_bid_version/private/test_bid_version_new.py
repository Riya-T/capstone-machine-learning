"""Hidden tests for the c_bid_version change (versioned bids). Never shown to
the writer or the editor.

Usage (with auction.py importable, e.g. in the sandbox):
    python -m pytest changes/c_bid_version/private/test_bid_version_new.py
"""

import pytest
from auction import AuctionError, AuctionHouse, BidTooLow, VersionConflict


@pytest.fixture
def house():
    h = AuctionHouse()
    h.add_lot("vase", 500)
    h.add_lot("clock", 200)
    return h


def state(h):
    return {lot: (h.get_bids(lot), h.get_version(lot)) for lot in h.get_lots()}


def test_version_starts_at_one(house):
    assert house.get_version("vase") == 1
    assert house.get_version("clock") == 1


def test_version_counts_every_accepted_bid(house):
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 510)
    house.place_bid("vase", "alice", 520)
    assert house.get_version("vase") == 4


def test_version_matching_bid_is_accepted(house):
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 600, expected_version=2)
    assert house.get_highest_bid("vase") == ("bob", 600)
    assert house.get_version("vase") == 3


def test_version_lots_are_independent(house):
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 510)
    assert house.get_version("clock") == 1
    house.place_bid("clock", "alice", 200, expected_version=1)
    assert house.get_version("vase") == 3
    assert house.get_version("clock") == 2


@pytest.mark.parametrize("expected", [0, 2, 99])
def test_version_any_other_value_conflicts(house, expected):
    before = state(house)
    with pytest.raises(VersionConflict):
        house.place_bid("vase", "alice", 500, expected_version=expected)
    assert state(house) == before


def test_version_failed_bids_do_not_change_it(house):
    house.place_bid("vase", "alice", 500)
    for call in (
        lambda: house.place_bid("vase", "bob", 505),
        lambda: house.place_bid("vase", "alice", 900),
        lambda: house.place_bid("vase", "", 900),
        lambda: house.place_bid("vase", "bob", 900, expected_version=1),
    ):
        with pytest.raises((ValueError, AuctionError)):
            call()
    assert house.get_version("vase") == 2


def test_version_reads_do_not_change_it(house):
    house.place_bid("vase", "alice", 500)
    house.get_bids("vase")
    house.get_highest_bid("vase")
    house.get_leading_lots("alice")
    house.get_min_bid("vase")
    assert house.get_version("vase") == 2


def test_version_conflict_comes_after_key_and_value_errors(house):
    with pytest.raises(KeyError):
        house.place_bid("lamp", "alice", 500, expected_version=7)
    with pytest.raises(ValueError):
        house.place_bid("vase", "", 500, expected_version=7)
    with pytest.raises(ValueError):
        house.place_bid("vase", "alice", 0, expected_version=7)


def test_version_conflict_comes_before_bid_rules(house):
    house.place_bid("vase", "alice", 500)
    # too low and stale: the stale version wins
    with pytest.raises(VersionConflict):
        house.place_bid("vase", "bob", 501, expected_version=1)
    # the leader bidding again with a stale version
    with pytest.raises(VersionConflict):
        house.place_bid("vase", "alice", 900, expected_version=1)


def test_version_matching_still_applies_bid_rules(house):
    house.place_bid("vase", "alice", 500)
    with pytest.raises(BidTooLow):
        house.place_bid("vase", "bob", 505, expected_version=2)
    assert house.get_version("vase") == 2


def test_version_unknown_lot_raises_key_error(house):
    with pytest.raises(KeyError):
        house.get_version("lamp")


def test_version_conflict_is_an_auction_error():
    assert issubclass(VersionConflict, AuctionError)
    assert not issubclass(VersionConflict, BidTooLow)
