"""Public checks for the c_withdraw change (withdrawing bids). Shown to the
editor, never to the writer.

Usage (with auction.py importable, e.g. in the sandbox):
    python -m pytest changes/c_withdraw/public/test_withdraw_public.py
"""

import pytest
from auction import AuctionError, AuctionHouse


def test_withdrawing_the_top_bid_restores_the_one_below():
    house = AuctionHouse()
    house.add_lot("vase", 500)
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 600)
    house.withdraw_bid("vase", "bob")
    assert house.get_highest_bid("vase") == ("alice", 500)
    assert house.get_bids("vase") == [("alice", 500)]
    assert house.get_version("vase") == 4


def test_withdrawing_without_bids_raises():
    house = AuctionHouse()
    house.add_lot("vase", 500)
    with pytest.raises(AuctionError):
        house.withdraw_bid("vase", "alice")
    assert house.get_version("vase") == 1
