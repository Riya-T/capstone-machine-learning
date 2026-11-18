"""Hidden tests for the c_capacity change (hold capacities). Never shown to
the writer or the editor. They call only the spec's methods and this
change's own, never undo.

Usage (with ship.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from ship import CargoError, HoldFull, NotEnoughCrates, Ship


@pytest.fixture
def ship():
    s = Ship()
    s.add_hold("fore", capacity=10)
    s.add_hold("mid")
    s.add_hold("aft", capacity=6)
    s.load("fore", "grain", 4)
    s.load("fore", "steel", 2)
    s.load("mid", "coal", 5)
    return s


def state(s):
    return [(h, [(c, s.get_count(h, c)) for c in s.get_cargo(h)]) for h in s.get_holds()]


# --- setting and reading capacities ---------------------------------------------


def test_capacities_are_kept_per_hold(ship):
    assert ship.get_capacity("fore") == 10
    assert ship.get_capacity("mid") is None
    assert ship.get_capacity("aft") == 6


def test_the_capacity_can_be_given_by_position():
    s = Ship()
    s.add_hold("fore", 3)
    assert s.get_capacity("fore") == 3


def test_a_hold_without_a_capacity_has_no_limit():
    s = Ship()
    s.add_hold("fore")
    s.load("fore", "grain", 100000)
    assert s.get_capacity("fore") is None
    assert s.get_count("fore", "grain") == 100000


@pytest.mark.parametrize("capacity", [0, -4])
def test_a_capacity_of_0_or_less_is_rejected(ship, capacity):
    before = state(ship)
    with pytest.raises(ValueError):
        ship.add_hold("bow", capacity=capacity)
    assert state(ship) == before
    assert ship.get_holds() == ["fore", "mid", "aft"]


def test_get_capacity_of_a_hold_not_in_use_raises_key_error(ship):
    with pytest.raises(KeyError):
        ship.get_capacity("bow")
    ship.load("aft", "iron", 1)
    ship.seal_hold("aft", "mid")
    with pytest.raises(KeyError):
        ship.get_capacity("aft")


def test_hold_full_is_a_cargo_error_of_its_own():
    assert issubclass(HoldFull, CargoError)
    assert not issubclass(HoldFull, NotEnoughCrates)


# --- loading ------------------------------------------------------------------------


def test_loading_up_to_the_capacity_is_allowed(ship):
    ship.load("fore", "wool", 4)
    assert ship.get_count("fore", "wool") == 4
    ship.load("aft", "iron", 6)
    assert ship.get_count("aft", "iron") == 6


def test_loading_past_the_capacity_raises_and_changes_nothing(ship):
    before = state(ship)
    with pytest.raises(HoldFull):
        ship.load("fore", "wool", 5)
    with pytest.raises(HoldFull):
        ship.load("fore", "grain", 5)
    with pytest.raises(HoldFull):
        ship.load("aft", "iron", 7)
    assert state(ship) == before


def test_the_capacity_counts_every_cargo_type_together(ship):
    ship.load("aft", "iron", 2)
    ship.load("aft", "wool", 2)
    ship.load("aft", "coal", 2)
    with pytest.raises(HoldFull):
        ship.load("aft", "salt", 1)
    assert ship.get_cargo("aft") == ["coal", "iron", "wool"]


def test_unloading_frees_room(ship):
    ship.load("fore", "wool", 4)
    ship.unload("fore", "grain", 3)
    ship.load("fore", "salt", 3)
    assert ship.get_count("fore", "salt") == 3


def test_unloading_is_never_limited(ship):
    ship.unload("fore", "grain", 4)
    ship.unload("fore", "steel", 1)
    assert ship.get_cargo("fore") == ["steel"]


# --- shifting and sealing ---------------------------------------------------------


def test_shift_all_into_a_hold_with_room_works(ship):
    assert ship.shift_all("fore", "aft") == 6
    assert ship.get_count("aft", "grain") == 4
    assert ship.get_cargo("fore") == []


def test_shift_all_past_the_capacity_moves_nothing(ship):
    before = state(ship)
    with pytest.raises(HoldFull):
        ship.shift_all("mid", "fore")
    assert state(ship) == before


def test_shift_all_counts_what_is_already_in_the_receiving_hold(ship):
    ship.load("aft", "iron", 1)
    before = state(ship)
    with pytest.raises(HoldFull):
        ship.shift_all("fore", "aft")
    assert state(ship) == before


def test_shift_all_out_of_a_hold_is_never_limited(ship):
    ship.load("aft", "iron", 6)
    assert ship.shift_all("aft", "mid") == 6
    assert ship.get_count("mid", "iron") == 6


def test_seal_hold_into_a_hold_with_room_works(ship):
    ship.load("aft", "iron", 3)
    assert ship.seal_hold("aft", "fore") == 3
    assert ship.seal_hold("fore", "mid") == 9
    assert ship.get_holds() == ["mid"]
    assert ship.get_count("mid", "grain") == 4


def test_seal_hold_past_the_capacity_moves_nothing_and_keeps_the_hold(ship):
    ship.load("aft", "iron", 1)
    before = state(ship)
    with pytest.raises(HoldFull):
        ship.seal_hold("mid", "fore")
    with pytest.raises(HoldFull):
        ship.seal_hold("fore", "aft")
    assert state(ship) == before
    assert ship.get_holds() == ["fore", "mid", "aft"]
    assert ship.get_capacity("fore") == 10


def test_seal_hold_up_to_the_capacity_is_allowed(ship):
    ship.unload("mid", "coal", 1)
    assert ship.seal_hold("mid", "fore") == 4
    assert ship.get_count("fore", "coal") == 4
    with pytest.raises(HoldFull):
        ship.load("fore", "coal", 1)


def test_the_other_holds_keep_their_capacities_after_a_seal(ship):
    ship.load("aft", "iron", 2)
    ship.seal_hold("aft", "mid")
    assert ship.get_capacity("fore") == 10
    ship.add_hold("bow", capacity=2)
    assert ship.get_holds() == ["fore", "mid", "bow"]
    assert ship.get_capacity("bow") == 2
    with pytest.raises(HoldFull):
        ship.load("bow", "salt", 3)
