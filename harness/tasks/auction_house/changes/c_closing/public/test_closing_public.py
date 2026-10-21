"""Public checks for the c_closing change (closed lots). Shown to the editor,
never to the writer.

Usage (with auction.py importable, e.g. in the sandbox):
    python -m pytest changes/c_closing/public/test_closing_public.py
"""

import pytest
from auction import AuctionHouse, LotClosed


def test_closing_names_the_winner_and_stops_bidding():
    house = AuctionHouse()
    house.add_lot("vase", 500)
    house.place_bid("vase", "alice", 500)
    house.place_bid("vase", "bob", 600)
    assert house.close_lot("vase") == "bob"
    assert house.is_closed("vase")
    assert house.get_winner("vase") == "bob"
    with pytest.raises(LotClosed):
        house.place_bid("vase", "alice", 700)
    assert house.get_highest_bid("vase") == ("bob", 600)


def test_a_lot_without_bids_closes_without_a_winner():
    house = AuctionHouse()
    house.add_lot("vase", 500)
    house.add_lot("clock", 200)
    assert house.close_lot("vase") is None
    assert house.get_open_lots() == ["clock"]
    assert house.get_lots() == ["vase", "clock"]
