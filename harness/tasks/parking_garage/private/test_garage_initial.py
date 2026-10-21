"""Hidden tests for the initial parking_garage spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with garage.py importable, e.g. in the sandbox):
    python -m pytest private/test_garage_initial.py
"""

import pytest
from garage import Garage, GarageError, GarageFull

BAD_NAMES = ["", None, 7]
BAD_MINUTES = [-1, 2.5, "10", None]


@pytest.fixture
def garage():
    gar = Garage()
    gar.add_level("P1", 2)
    gar.add_level("P2", 1)
    return gar


def state(gar):
    """Every level's free spots and vehicles, to check that a failed call changed nothing."""
    return {lvl: (gar.get_free_spots(lvl), gar.get_vehicles(lvl)) for lvl in gar.get_levels()}


# --- levels -----------------------------------------------------------------


def test_a_new_level_is_empty(garage):
    assert garage.get_free_spots("P1") == 2
    assert garage.get_vehicles("P1") == []


def test_levels_are_listed_in_the_order_added():
    gar = Garage()
    for name in ["roof", "P1", "basement"]:
        gar.add_level(name, 3)
    assert gar.get_levels() == ["roof", "P1", "basement"]


@pytest.mark.parametrize("bad_id", BAD_NAMES)
def test_invalid_level_ids_are_rejected(bad_id):
    gar = Garage()
    with pytest.raises(ValueError):
        gar.add_level(bad_id, 5)
    assert gar.get_levels() == []


@pytest.mark.parametrize("spots", [0, -3, 1.5, "4", None])
def test_invalid_spot_counts_are_rejected(spots):
    gar = Garage()
    with pytest.raises(ValueError):
        gar.add_level("P1", spots)
    assert gar.get_levels() == []


def test_adding_a_level_twice_is_rejected(garage):
    garage.enter("AAA", 5)
    with pytest.raises(GarageError):
        garage.add_level("P1", 10)
    assert garage.get_levels() == ["P1", "P2"]
    assert garage.get_free_spots("P1") == 1


def test_a_bad_spot_count_is_reported_before_a_duplicate_id(garage):
    with pytest.raises(ValueError):
        garage.add_level("P1", 0)


@pytest.mark.parametrize("level_id", ["P9", None, 1])
def test_levels_that_were_not_added_raise_key_error(garage, level_id):
    with pytest.raises(KeyError):
        garage.get_free_spots(level_id)
    with pytest.raises(KeyError):
        garage.get_vehicles(level_id)


# --- entering ---------------------------------------------------------------


def test_entering_takes_the_first_level_with_a_free_spot(garage):
    assert garage.enter("AAA", 1) == "P1"
    assert garage.enter("BBB", 2) == "P1"
    assert garage.enter("CCC", 3) == "P2"
    assert garage.get_level("AAA") == "P1"
    assert garage.get_level("CCC") == "P2"
    assert garage.get_free_spots("P1") == 0
    assert garage.get_free_spots("P2") == 0


def test_vehicles_are_listed_in_entry_order(garage):
    garage.enter("BBB", 1)
    garage.enter("AAA", 2)
    assert garage.get_vehicles("P1") == ["BBB", "AAA"]
    assert garage.get_vehicles("P2") == []


def test_a_full_garage_raises_and_changes_nothing(garage):
    for plate in ["AAA", "BBB", "CCC"]:
        garage.enter(plate, 1)
    before = state(garage)
    with pytest.raises(GarageFull):
        garage.enter("DDD", 2)
    assert state(garage) == before
    with pytest.raises(KeyError):
        garage.get_level("DDD")


@pytest.mark.parametrize("plate", BAD_NAMES)
def test_invalid_plates_are_rejected(garage, plate):
    before = state(garage)
    with pytest.raises(ValueError):
        garage.enter(plate, 5)
    assert state(garage) == before


@pytest.mark.parametrize("minute", BAD_MINUTES)
def test_invalid_entry_minutes_are_rejected(garage, minute):
    before = state(garage)
    with pytest.raises(ValueError):
        garage.enter("AAA", minute)
    assert state(garage) == before


def test_a_parked_plate_cannot_enter_again(garage):
    garage.enter("AAA", 5)
    before = state(garage)
    with pytest.raises(GarageError):
        garage.enter("AAA", 6)
    assert state(garage) == before
    assert garage.get_level("AAA") == "P1"


def test_a_bad_plate_is_reported_before_a_full_garage(garage):
    for plate in ["AAA", "BBB", "CCC"]:
        garage.enter(plate, 1)
    with pytest.raises(ValueError):
        garage.enter("", 2)
    with pytest.raises(ValueError):
        garage.enter("DDD", -1)


def test_already_parked_is_reported_before_a_full_garage(garage):
    for plate in ["AAA", "BBB", "CCC"]:
        garage.enter(plate, 1)
    with pytest.raises(GarageError) as info:
        garage.enter("AAA", 2)
    assert not isinstance(info.value, GarageFull)


# --- leaving ----------------------------------------------------------------


def test_leaving_returns_the_minutes_parked(garage):
    garage.enter("AAA", 30)
    garage.enter("BBB", 45)
    assert garage.leave("AAA", 100) == 70
    assert garage.leave("BBB", 45) == 0


def test_leaving_frees_the_spot_for_the_next_vehicle(garage):
    garage.enter("AAA", 1)
    garage.enter("BBB", 2)
    garage.leave("AAA", 3)
    assert garage.get_free_spots("P1") == 1
    assert garage.get_vehicles("P1") == ["BBB"]
    assert garage.enter("CCC", 4) == "P1"
    assert garage.get_vehicles("P1") == ["BBB", "CCC"]


def test_a_plate_may_enter_again_after_leaving(garage):
    garage.enter("AAA", 1)
    garage.leave("AAA", 2)
    with pytest.raises(KeyError):
        garage.get_level("AAA")
    assert garage.enter("AAA", 3) == "P1"
    assert garage.leave("AAA", 10) == 7


@pytest.mark.parametrize("plate", ["ZZZ", None, 1])
def test_leaving_with_a_plate_that_is_not_parked_raises_key_error(garage, plate):
    garage.enter("AAA", 1)
    before = state(garage)
    with pytest.raises(KeyError):
        garage.leave(plate, 5)
    with pytest.raises(KeyError):
        garage.get_level(plate)
    assert state(garage) == before


@pytest.mark.parametrize("minute", [99, 2.5, "200", None])
def test_invalid_leaving_minutes_are_rejected(garage, minute):
    garage.enter("AAA", 100)
    before = state(garage)
    with pytest.raises(ValueError):
        garage.leave("AAA", minute)
    assert state(garage) == before
    assert garage.get_level("AAA") == "P1"


def test_an_unparked_plate_is_reported_before_a_bad_minute(garage):
    with pytest.raises(KeyError):
        garage.leave("ZZZ", -1)


# --- general ----------------------------------------------------------------


def test_garage_full_is_a_garage_error():
    assert issubclass(GarageFull, GarageError)


def test_garages_do_not_share_levels():
    first, second = Garage(), Garage()
    first.add_level("P1", 1)
    first.enter("AAA", 1)
    assert second.get_levels() == []
    second.add_level("P1", 1)
    assert second.get_free_spots("P1") == 1
