"""Hidden tests for the c_accepts change (destinations a bin accepts). Never
shown to the writer or the editor.

Usage (with sorting.py importable, e.g. in the sandbox):
    python -m pytest changes/c_accepts/private/test_accepts_new.py
"""

import pytest
from sorting import NotAccepted, SortingError, SortingRoom

BAD_SETTINGS = ["NY-", 5, ["NY-", ""], ["NY-", None], [3]]


@pytest.fixture
def room():
    # east holds NY-1, LA-2, NY-3: the refused parcel is in the middle.
    r = SortingRoom()
    for name in ["east", "west", "spare"]:
        r.add_bin(name)
    for parcel in ["NY-1", "LA-2", "NY-3"]:
        r.drop("east", parcel)
    r.drop("west", "SF-4")
    return r


def state(r):
    return [(b, list(r.get_parcels(b))) for b in list(r.get_bins())]


# --- the setting ------------------------------------------------------------


def test_every_bin_starts_accepting_every_parcel(room):
    assert [room.get_accepts(b) for b in room.get_bins()] == [None, None, None]
    room.add_bin("north")
    assert room.get_accepts("north") is None
    room.drop("north", "TX-7")
    assert room.get_parcels("north") == ["TX-7"]


def test_a_bin_added_again_after_closing_accepts_every_parcel(room):
    room.set_accepts("spare", ["NY-"])
    room.close_bin("spare", "west")
    room.add_bin("spare")
    assert room.get_accepts("spare") is None
    room.drop("spare", "TX-7")
    assert room.get_parcels("spare") == ["TX-7"]


def test_get_accepts_is_alphabetical_without_duplicates(room):
    room.set_accepts("spare", ["SF-", "NY-", "SF-", "BOS-"])
    assert room.get_accepts("spare") == ["BOS-", "NY-", "SF-"]


def test_each_setting_replaces_the_one_before(room):
    room.set_accepts("spare", ["NY-"])
    room.set_accepts("spare", ["LA-"])
    assert room.get_accepts("spare") == ["LA-"]
    with pytest.raises(NotAccepted):
        room.drop("spare", "NY-9")
    room.set_accepts("spare", None)
    assert room.get_accepts("spare") is None
    room.drop("spare", "NY-9")
    assert room.get_parcels("spare") == ["NY-9"]


def test_an_empty_list_accepts_no_parcel(room):
    room.set_accepts("spare", [])
    assert room.get_accepts("spare") == []
    before = state(room)
    with pytest.raises(NotAccepted):
        room.drop("spare", "NY-9")
    with pytest.raises(NotAccepted):
        room.empty_bin_into("west", "spare")
    assert state(room) == before


def test_prefixes_match_the_start_of_the_name_and_case_matters(room):
    room.set_accepts("spare", ["NY-"])
    for parcel in ["XNY-5", "ny-5", "NY5"]:
        with pytest.raises(NotAccepted):
            room.drop("spare", parcel)
    room.drop("spare", "NY-5")
    assert room.get_parcels("spare") == ["NY-5"]


@pytest.mark.parametrize("setting", BAD_SETTINGS)
def test_invalid_settings_are_rejected_and_keep_the_old_one(room, setting):
    room.set_accepts("spare", ["NY-"])
    with pytest.raises(ValueError):
        room.set_accepts("spare", setting)
    assert room.get_accepts("spare") == ["NY-"]


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.set_accepts("north", ["NY-"]),
        lambda r: r.set_accepts("north", None),
        lambda r: r.get_accepts("north"),
        lambda r: r.set_accepts("spare", ["NY-"]),  # closed below
        lambda r: r.get_accepts("spare"),
    ],
)
def test_bins_not_in_use_raise_key_error(room, call):
    room.close_bin("spare", "west")
    with pytest.raises(KeyError):
        call(room)


def test_a_setting_moves_no_parcels(room):
    before = state(room)
    room.set_accepts("east", ["TX-"])
    room.set_accepts("west", [])
    assert state(room) == before


# --- drop ---------------------------------------------------------------------


def test_drop_of_an_accepted_parcel_works(room):
    room.set_accepts("spare", ["NY-", "LA-"])
    room.drop("spare", "LA-7")
    room.drop("spare", "NY-8")
    assert room.get_parcels("spare") == ["LA-7", "NY-8"]


def test_drop_of_a_refused_parcel_changes_nothing(room):
    room.set_accepts("spare", ["NY-", "LA-"])
    before = state(room)
    with pytest.raises(NotAccepted):
        room.drop("spare", "SF-7")
    assert state(room) == before


def test_a_refused_parcel_is_not_in_the_room(room):
    room.set_accepts("spare", ["NY-"])
    with pytest.raises(NotAccepted):
        room.drop("spare", "TX-7")
    room.drop("west", "TX-7")
    assert room.get_parcels("west") == ["SF-4", "TX-7"]


# --- empty_bin_into and close_bin -----------------------------------------


def test_empty_bin_into_a_bin_that_accepts_every_parcel(room):
    room.set_accepts("spare", ["LA-", "NY-"])
    assert room.empty_bin_into("east", "spare") == 3
    assert room.get_parcels("spare") == ["NY-1", "LA-2", "NY-3"]


def test_empty_bin_into_with_one_refused_parcel_moves_nothing(room):
    room.set_accepts("spare", ["NY-"])
    before = state(room)
    with pytest.raises(NotAccepted):
        room.empty_bin_into("east", "spare")
    assert state(room) == before
    assert room.get_parcels("spare") == []


def test_close_bin_into_a_bin_that_accepts_every_parcel(room):
    room.set_accepts("west", ["NY-", "LA-", "SF-"])
    assert room.close_bin("east", "west") == 3
    assert room.get_bins() == ["west", "spare"]
    assert room.get_parcels("west") == ["SF-4", "NY-1", "LA-2", "NY-3"]


def test_close_bin_with_one_refused_parcel_moves_nothing_and_keeps_it(room):
    room.set_accepts("west", ["NY-", "SF-"])
    before = state(room)
    with pytest.raises(NotAccepted):
        room.close_bin("east", "west")
    assert state(room) == before
    assert room.get_bins() == ["east", "west", "spare"]


def test_a_refused_close_can_be_retried_once_the_parcels_are_accepted(room):
    room.set_accepts("spare", ["NY-"])
    with pytest.raises(NotAccepted):
        room.close_bin("east", "spare")
    room.set_accepts("spare", ["NY-", "LA-"])
    assert room.close_bin("east", "spare") == 3
    assert room.get_bins() == ["west", "spare"]


def test_an_empty_bin_never_raises_not_accepted(room):
    room.set_accepts("east", [])
    assert room.empty_bin_into("spare", "east") == 0
    assert room.close_bin("spare", "east") == 0
    assert room.get_bins() == ["east", "west"]


# --- parcels already there --------------------------------------------------


def test_parcels_already_in_a_bin_are_not_affected(room):
    room.set_accepts("east", ["TX-"])
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]
    assert room.pick("east") == "NY-1"
    assert room.recall("NY-3") == "east"
    assert room.empty_bin_into("east", "spare") == 1
    with pytest.raises(NotAccepted):
        room.drop("east", "NY-1")


def test_the_setting_of_the_bin_parcels_leave_is_not_checked(room):
    room.set_accepts("east", [])
    room.set_accepts("west", ["SF-"])
    assert room.empty_bin_into("east", "spare") == 3
    assert room.close_bin("west", "spare") == 1
    assert room.get_parcels("spare") == ["NY-1", "LA-2", "NY-3", "SF-4"]


def test_not_accepted_is_a_sorting_error():
    assert issubclass(NotAccepted, SortingError)
