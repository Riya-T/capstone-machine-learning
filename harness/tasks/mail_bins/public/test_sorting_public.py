"""Public checks for sorting.py.

Usage (with sorting.py importable, e.g. in the sandbox):
    python -m pytest public/test_sorting_public.py
"""

import pytest
from sorting import SortingError, SortingRoom


@pytest.fixture
def room():
    r = SortingRoom()
    r.add_bin("east")
    r.add_bin("west")
    for parcel in ["NY-1", "LA-2", "NY-3"]:
        r.drop("east", parcel)
    return r


def test_parcels_wait_in_arrival_order_and_the_first_is_picked_first(room):
    assert room.get_bins() == ["east", "west"]
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]
    assert room.pick("east") == "NY-1"
    assert room.get_parcels("east") == ["LA-2", "NY-3"]


def test_a_parcel_in_the_bin_cannot_be_dropped_again(room):
    with pytest.raises(SortingError):
        room.drop("east", "LA-2")
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]


def test_recall_removes_a_parcel_from_the_middle(room):
    assert room.recall("LA-2") == "east"
    assert room.get_parcels("east") == ["NY-1", "NY-3"]


def test_empty_bin_into_moves_every_parcel_behind_the_others(room):
    room.drop("west", "SF-4")
    assert room.empty_bin_into("east", "west") == 3
    assert room.get_parcels("west") == ["SF-4", "NY-1", "LA-2", "NY-3"]
    assert room.get_parcels("east") == []


def test_a_closed_bin_is_gone_and_its_name_is_free(room):
    assert room.close_bin("east", "west") == 3
    assert room.get_bins() == ["west"]
    assert room.get_parcels("west") == ["NY-1", "LA-2", "NY-3"]
    with pytest.raises(KeyError):
        room.get_parcels("east")
    room.add_bin("east")
    assert room.get_bins() == ["west", "east"]
    assert room.get_parcels("east") == []
    assert room.close_bin("east", "west") == 0  # an empty bin is closed too
    assert room.get_bins() == ["west"]


def test_picking_from_an_empty_bin_raises(room):
    with pytest.raises(SortingError):
        room.pick("west")
