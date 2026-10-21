"""Hidden tests for the c_sizes change (vehicle and level sizes). Never shown
to the writer or the editor.

Usage (with garage.py importable, e.g. in the sandbox):
    python -m pytest changes/c_sizes/private/test_sizes_new.py
"""

import pytest
from garage import Garage, GarageError, GarageFull

BAD_SIZES = ["tiny", "LARGE", "", None, 1]


@pytest.fixture
def garage():
    gar = Garage()
    gar.add_level("P1", 2, max_size="small")
    gar.add_level("P2", 1, max_size="medium")
    gar.add_level("P3", 2, max_size="large")
    return gar


def state(gar):
    return {lvl: (gar.get_free_spots(lvl), gar.get_vehicles(lvl)) for lvl in gar.get_levels()}


def test_each_vehicle_takes_the_first_level_it_fits_on(garage):
    assert garage.enter("S1", 1, size="small") == "P1"
    assert garage.enter("M1", 2, size="medium") == "P2"
    assert garage.enter("L1", 3, size="large") == "P3"
    assert garage.enter("M2", 4, size="medium") == "P3"
    assert garage.enter("S2", 5, size="small") == "P1"
    assert garage.get_vehicles("P1") == ["S1", "S2"]
    assert garage.get_vehicles("P3") == ["L1", "M2"]


def test_no_fitting_level_with_a_spot_raises_garage_full(garage):
    garage.enter("L1", 1, size="large")
    garage.enter("L2", 2, size="large")
    before = state(garage)
    with pytest.raises(GarageFull):
        garage.enter("L3", 3, size="large")
    assert state(garage) == before
    assert garage.get_free_spots("P1") == 2


def test_a_freed_spot_is_taken_by_the_next_vehicle_that_fits(garage):
    garage.enter("L1", 1, size="large")
    garage.enter("L2", 2, size="large")
    garage.leave("L1", 3)
    assert garage.enter("L3", 4, size="large") == "P3"
    assert garage.get_vehicles("P3") == ["L2", "L3"]


@pytest.mark.parametrize("size", BAD_SIZES)
def test_bad_vehicle_sizes_are_rejected(garage, size):
    before = state(garage)
    with pytest.raises(ValueError):
        garage.enter("AAA", 1, size=size)
    assert state(garage) == before
    with pytest.raises(KeyError):
        garage.get_size("AAA")


@pytest.mark.parametrize("max_size", BAD_SIZES)
def test_bad_level_sizes_are_rejected(garage, max_size):
    with pytest.raises(ValueError):
        garage.add_level("P4", 3, max_size=max_size)
    assert garage.get_levels() == ["P1", "P2", "P3"]


def test_get_max_size_reports_each_level(garage):
    assert [garage.get_max_size(lvl) for lvl in garage.get_levels()] == [
        "small",
        "medium",
        "large",
    ]


@pytest.mark.parametrize("level_id", ["P9", None, 1])
def test_get_max_size_of_a_missing_level_raises_key_error(garage, level_id):
    with pytest.raises(KeyError):
        garage.get_max_size(level_id)


def test_get_size_reports_a_parked_vehicle_until_it_leaves(garage):
    garage.enter("AAA", 1, size="small")
    garage.enter("BBB", 2)
    assert garage.get_size("AAA") == "small"
    assert garage.get_size("BBB") == "medium"
    garage.leave("AAA", 5)
    with pytest.raises(KeyError):
        garage.get_size("AAA")
    for plate in ["ZZZ", None, 1]:
        with pytest.raises(KeyError):
            garage.get_size(plate)


def test_a_bad_size_is_reported_before_already_parked(garage):
    garage.enter("AAA", 1)
    with pytest.raises(ValueError):
        garage.enter("AAA", 2, size="tiny")


def test_already_parked_is_reported_before_no_fitting_level(garage):
    garage.enter("L1", 1, size="large")
    garage.enter("L2", 2, size="large")
    with pytest.raises(GarageError) as info:
        garage.enter("L1", 3, size="large")
    assert not isinstance(info.value, GarageFull)


def test_a_bad_level_size_is_reported_before_a_duplicate_id(garage):
    with pytest.raises(ValueError):
        garage.add_level("P1", 3, max_size="huge")
    assert garage.get_max_size("P1") == "small"
