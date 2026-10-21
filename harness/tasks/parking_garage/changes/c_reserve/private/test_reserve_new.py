"""Hidden tests for the c_reserve change (reserved spots). Never shown to the
writer or the editor.

Usage (with garage.py importable, e.g. in the sandbox):
    python -m pytest changes/c_reserve/private/test_reserve_new.py
"""

import pytest
from garage import Garage, GarageError, GarageFull


@pytest.fixture
def garage():
    gar = Garage()
    gar.add_level("P1", 2)
    gar.add_level("P2", 2)
    return gar


def state(gar):
    return {
        lvl: (gar.get_free_spots(lvl), gar.get_vehicles(lvl), gar.get_reserved(lvl))
        for lvl in gar.get_levels()
    }


def test_a_new_garage_has_no_reservations(garage):
    assert garage.get_reserved("P1") == []
    assert not garage.has_reservation("AAA")


def test_reserving_takes_a_free_spot_on_that_level_only(garage):
    garage.reserve("P1", "AAA")
    assert garage.get_free_spots("P1") == 1
    assert garage.get_free_spots("P2") == 2
    assert garage.get_vehicles("P1") == []


def test_reserved_plates_are_listed_in_reservation_order(garage):
    garage.reserve("P1", "BBB")
    garage.reserve("P2", "CCC")
    garage.reserve("P1", "AAA")
    assert garage.get_reserved("P1") == ["BBB", "AAA"]
    assert garage.get_reserved("P2") == ["CCC"]


def test_a_fully_reserved_level_is_full_for_other_vehicles(garage):
    garage.reserve("P1", "AAA")
    garage.reserve("P1", "BBB")
    assert garage.enter("CCC", 1) == "P2"
    assert garage.enter("DDD", 2) == "P2"
    before = state(garage)
    with pytest.raises(GarageFull):
        garage.enter("EEE", 3)
    assert state(garage) == before


def test_entering_with_a_reservation_uses_the_held_spot(garage):
    garage.reserve("P2", "AAA")
    assert garage.enter("AAA", 1) == "P2"
    assert garage.get_free_spots("P2") == 1
    assert garage.get_vehicles("P2") == ["AAA"]
    assert garage.get_level("AAA") == "P2"
    assert not garage.has_reservation("AAA")
    assert garage.get_reserved("P2") == []


@pytest.mark.parametrize("level_id", ["P9", None, 1])
def test_reserving_on_a_missing_level_raises_key_error(garage, level_id):
    before = state(garage)
    with pytest.raises(KeyError):
        garage.reserve(level_id, "AAA")
    with pytest.raises(KeyError):
        garage.get_reserved(level_id)
    assert state(garage) == before
    assert not garage.has_reservation("AAA")


@pytest.mark.parametrize("plate", ["", None, 7])
def test_reserving_with_a_bad_plate_raises_value_error(garage, plate):
    before = state(garage)
    with pytest.raises(ValueError):
        garage.reserve("P1", plate)
    assert state(garage) == before


def test_a_parked_or_reserved_plate_cannot_reserve_again(garage):
    garage.enter("AAA", 1)
    garage.reserve("P2", "BBB")
    before = state(garage)
    with pytest.raises(GarageError):
        garage.reserve("P1", "AAA")
    with pytest.raises(GarageError):
        garage.reserve("P1", "BBB")
    assert state(garage) == before


def test_reserving_on_a_level_without_a_free_spot_raises(garage):
    garage.enter("AAA", 1)
    garage.reserve("P1", "BBB")
    before = state(garage)
    with pytest.raises(GarageFull):
        garage.reserve("P1", "CCC")
    assert state(garage) == before


def test_a_reserved_plate_is_not_parked(garage):
    garage.reserve("P1", "AAA")
    assert garage.get_vehicles("P1") == []
    with pytest.raises(KeyError):
        garage.get_level("AAA")
    with pytest.raises(KeyError):
        garage.leave("AAA", 5)
    assert garage.has_reservation("AAA")


@pytest.mark.parametrize("plate", ["ZZZ", None, 1])
def test_cancelling_without_a_reservation_raises_key_error(garage, plate):
    garage.reserve("P1", "AAA")
    before = state(garage)
    with pytest.raises(KeyError):
        garage.cancel_reservation(plate)
    assert state(garage) == before
    assert not garage.has_reservation(plate)


def test_cancelling_removes_only_that_reservation(garage):
    garage.reserve("P1", "AAA")
    garage.reserve("P1", "BBB")
    garage.cancel_reservation("AAA")
    assert garage.get_reserved("P1") == ["BBB"]
    assert garage.get_free_spots("P1") == 1
    assert garage.enter("CCC", 1) == "P1"
    assert garage.enter("DDD", 2) == "P2"


def test_reserve_error_order(garage):
    garage.enter("AAA", 1)
    garage.enter("BBB", 2)
    with pytest.raises(KeyError):
        garage.reserve("P9", "")
    with pytest.raises(ValueError):
        garage.reserve("P1", "")
    with pytest.raises(GarageError) as info:
        garage.reserve("P1", "AAA")
    assert not isinstance(info.value, GarageFull)


def test_after_leaving_the_vehicle_enters_like_any_other(garage):
    garage.reserve("P2", "AAA")
    garage.enter("AAA", 1)
    assert garage.leave("AAA", 9) == 8
    assert garage.get_free_spots("P2") == 2
    assert garage.enter("AAA", 10) == "P1"
