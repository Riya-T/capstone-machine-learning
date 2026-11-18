"""Hidden tests for the c_lookup change (looking parcels up). Never shown to
the writer or the editor.

Usage (with sorting.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lookup/private/test_lookup_new.py
"""

import pytest
from sorting import SortingRoom


@pytest.fixture
def room():
    r = SortingRoom()
    for name in ["east", "west", "spare"]:
        r.add_bin(name)
    for parcel in ["NY-1", "LA-2", "NY-3"]:
        r.drop("east", parcel)
    r.drop("west", "SF-4")
    r.drop("west", "NY-5")
    return r


def state(r):
    return [(b, list(r.get_parcels(b))) for b in list(r.get_bins())]


# --- get_bin_of -------------------------------------------------------------


def test_get_bin_of_every_parcel(room):
    assert [room.get_bin_of(p) for p in ["NY-1", "LA-2", "NY-3", "SF-4", "NY-5"]] == [
        "east", "east", "east", "west", "west",
    ]  # fmt: skip


def test_get_bin_of_a_parcel_never_dropped_is_none(room):
    assert room.get_bin_of("TX-9") is None


def test_get_bin_of_a_picked_or_recalled_parcel_is_none(room):
    room.pick("east")
    room.recall("SF-4")
    assert room.get_bin_of("NY-1") is None
    assert room.get_bin_of("SF-4") is None
    assert room.get_bin_of("LA-2") == "east"


def test_get_bin_of_follows_moved_parcels(room):
    room.empty_bin_into("east", "spare")
    assert room.get_bin_of("LA-2") == "spare"
    room.close_bin("west", "spare")
    assert room.get_bin_of("NY-5") == "spare"
    room.recall("NY-3")
    room.drop("east", "NY-3")
    assert room.get_bin_of("NY-3") == "east"


def test_get_bin_of_a_parcel_in_a_bin_added_again(room):
    room.close_bin("spare", "east")
    room.add_bin("spare")
    room.drop("spare", "TX-7")
    assert room.get_bin_of("TX-7") == "spare"


# --- find_parcels -------------------------------------------------------------


def test_find_parcels_lists_bins_in_order_and_parcels_front_to_back(room):
    assert room.find_parcels("NY-") == ["NY-1", "NY-3", "NY-5"]


def test_find_parcels_follows_the_order_of_the_bins_not_of_arrival(room):
    room.drop("spare", "NY-0")
    room.drop("east", "NY-9")
    assert room.find_parcels("NY-") == ["NY-1", "NY-3", "NY-9", "NY-5", "NY-0"]


def test_find_parcels_after_moves(room):
    room.empty_bin_into("east", "west")
    assert room.find_parcels("NY-") == ["NY-5", "NY-1", "NY-3"]
    room.close_bin("west", "spare")
    assert room.find_parcels("NY-") == ["NY-5", "NY-1", "NY-3"]
    assert room.find_parcels("NY-", "spare") == ["NY-5", "NY-1", "NY-3"]


def test_a_whole_name_is_a_prefix_of_itself(room):
    assert room.find_parcels("LA-2") == ["LA-2"]


def test_prefixes_match_the_start_and_case_matters(room):
    assert room.find_parcels("ny-") == []
    assert room.find_parcels("-1") == []
    assert room.find_parcels("S") == ["SF-4"]


def test_find_parcels_with_no_match_is_empty(room):
    assert room.find_parcels("TX-") == []
    assert room.find_parcels("NY-", "spare") == []


def test_find_parcels_in_one_bin(room):
    assert room.find_parcels("NY-", "east") == ["NY-1", "NY-3"]
    assert room.find_parcels("NY-", "west") == ["NY-5"]
    assert room.find_parcels("LA-", "west") == []


def test_picked_and_recalled_parcels_are_not_found(room):
    room.pick("east")
    room.recall("NY-5")
    assert room.find_parcels("NY-") == ["NY-3"]


@pytest.mark.parametrize("bin_name", ["north", "spare"])
def test_find_parcels_in_a_bin_not_in_use_raises_key_error(room, bin_name):
    room.close_bin("spare", "east")
    with pytest.raises(KeyError):
        room.find_parcels("NY-", bin_name)


def test_lookups_change_nothing(room):
    before = state(room)
    room.get_bin_of("NY-1")
    room.get_bin_of("TX-9")
    room.find_parcels("NY-")
    room.find_parcels("NY-", "east")
    assert state(room) == before
    assert room.pick("east") == "NY-1"
