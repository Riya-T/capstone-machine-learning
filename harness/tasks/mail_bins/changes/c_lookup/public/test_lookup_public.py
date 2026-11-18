"""Public checks for the c_lookup change (looking parcels up). Shown to the
editor, never to the writer.

Usage (with sorting.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lookup/public/test_lookup_public.py
"""

import pytest
from sorting import SortingRoom


@pytest.fixture
def room():
    r = SortingRoom()
    r.add_bin("east")
    r.add_bin("west")
    for parcel in ["NY-1", "LA-2", "NY-3"]:
        r.drop("east", parcel)
    r.drop("west", "NY-4")
    return r


def test_get_bin_of_tells_where_a_parcel_waits(room):
    assert room.get_bin_of("LA-2") == "east"
    assert room.get_bin_of("NY-4") == "west"
    assert room.get_bin_of("TX-9") is None


def test_find_parcels_lists_matches_bin_by_bin(room):
    assert room.find_parcels("NY-") == ["NY-1", "NY-3", "NY-4"]
    assert room.find_parcels("NY-", "west") == ["NY-4"]
    assert room.find_parcels("SF-") == []
