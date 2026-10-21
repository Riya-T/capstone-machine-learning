"""Public checks for the c_bid_version change (versioned bids). Shown to the
editor, never to the writer.

Usage (with auction.py importable, e.g. in the sandbox):
    python -m pytest changes/c_bid_version/public/test_bid_version_public.py
"""

import pytest
from auction import AuctionHouse, VersionConflict


def test_each_bid_raises_the_version():
    house = AuctionHouse()
    house.add_lot("vase", 500)
    assert house.get_version("vase") == 1
    house.place_bid("vase", "alice", 500, expected_version=1)
    assert house.get_version("vase") == 2


def test_a_stale_version_is_refused():
    house = AuctionHouse()
    house.add_lot("vase", 500)
    house.place_bid("vase", "alice", 500)
    with pytest.raises(VersionConflict):
        house.place_bid("vase", "bob", 600, expected_version=1)
    assert house.get_highest_bid("vase") == ("alice", 500)
    assert house.get_version("vase") == 2
