"""Public checks for the c_increment change (adjustable minimum raise).
Shown to the editor, never to the writer.

Usage (with auction.py importable, e.g. in the sandbox):
    python -m pytest changes/c_increment/public/test_increment_public.py
"""

import pytest
from auction import AuctionHouse, BidTooLow


def test_the_house_sets_the_minimum_raise():
    house = AuctionHouse(min_increment=50)
    house.add_lot("vase", 500)
    house.place_bid("vase", "alice", 500)
    assert house.get_min_increment("vase") == 50
    assert house.get_min_bid("vase") == 550
    with pytest.raises(BidTooLow):
        house.place_bid("vase", "bob", 549)
    house.place_bid("vase", "bob", 550)
    assert house.get_highest_bid("vase") == ("bob", 550)


def test_a_lot_can_set_its_own_minimum_raise():
    house = AuctionHouse()
    house.add_lot("vase", 500, min_increment=1)
    house.add_lot("clock", 200)
    assert house.get_min_increment("vase") == 1
    assert house.get_min_increment("clock") == 10
    assert house.get_min_bid("clock") == 200
