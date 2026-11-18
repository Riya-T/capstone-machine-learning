"""Hidden tests for the c_capacity change (fridge capacity). Never shown to
the writer or the editor.

Usage (with blood_bank.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_bank_capacity_new.py
"""

import pytest
from blood_bank import BloodBank, BloodBankError, FridgeFull, NotEnoughUnits


@pytest.fixture
def bank():
    # ward holds 7 of its 10, lab 4 with no limit, theatre is empty with room for 5.
    b = BloodBank()
    b.add_fridge("ward", capacity=10)
    b.add_fridge("lab")
    b.add_fridge("theatre", capacity=5)
    b.store("ward", "O-", 5)
    b.store("ward", "A+", 2)
    b.store("lab", "B+", 4)
    return b


def held(b, fridge):
    """The blood types the fridge holds units of, with their units. Blood
    types listed with 0 units are left out: listing them is unspecified."""
    return [(t, b.get_units(fridge, t)) for t in b.get_blood_types(fridge) if b.get_units(fridge, t)]


def state(b):
    return [(f, held(b, f)) for f in b.get_fridges()]


# --- the setting --------------------------------------------------------------


def test_capacity_defaults_to_none():
    b = BloodBank()
    b.add_fridge("ward")
    assert b.get_capacity("ward") is None
    b.store("ward", "O-", 1000)
    assert b.get_units("ward", "O-") == 1000


def test_capacity_of_each_fridge_is_its_own(bank):
    assert [bank.get_capacity(f) for f in bank.get_fridges()] == [10, None, 5]


@pytest.mark.parametrize("capacity", [0, -4])
def test_capacity_must_be_greater_than_0(bank, capacity):
    before = state(bank)
    with pytest.raises(ValueError):
        bank.add_fridge("cellar", capacity=capacity)
    assert state(bank) == before
    assert bank.get_fridges() == ["ward", "lab", "theatre"]


def test_capacity_of_a_fridge_not_in_use_raises_key_error(bank):
    with pytest.raises(KeyError):
        bank.get_capacity("cellar")
    bank.retire_fridge("theatre", "lab")
    with pytest.raises(KeyError):
        bank.get_capacity("theatre")


def test_capacity_error_is_a_blood_bank_error():
    assert issubclass(FridgeFull, BloodBankError)
    assert not issubclass(FridgeFull, NotEnoughUnits)


# --- store ----------------------------------------------------------------------


def test_capacity_can_be_filled_exactly(bank):
    bank.store("ward", "AB-", 3)
    assert bank.get_units("ward", "AB-") == 3
    with pytest.raises(FridgeFull):
        bank.store("ward", "AB-", 1)


def test_capacity_counts_every_blood_type_together(bank):
    before = state(bank)
    with pytest.raises(FridgeFull):
        bank.store("ward", "B-", 4)
    assert state(bank) == before


def test_capacity_frees_up_when_units_are_taken(bank):
    bank.take("ward", "O-", 3)
    bank.store("ward", "B-", 6)
    assert bank.get_units("ward", "B-") == 6


def test_capacity_does_not_stop_taking_units(bank):
    bank.take("ward", "O-", 5)
    bank.take("ward", "A+", 2)
    assert held(bank, "ward") == []


# --- transfer_all ---------------------------------------------------------------


def test_capacity_allows_a_transfer_that_fits(bank):
    bank.take("ward", "O-", 1)
    assert bank.transfer_all("lab", "ward") == 4
    assert bank.get_units("ward", "B+") == 4
    assert held(bank, "lab") == []


def test_capacity_stops_a_transfer_that_does_not_fit_as_a_whole(bank):
    before = state(bank)
    with pytest.raises(FridgeFull):
        bank.transfer_all("ward", "theatre")
    assert state(bank) == before
    assert bank.get_units("theatre", "O-") == 0
    assert bank.get_units("ward", "A+") == 2


def test_capacity_is_not_checked_on_the_fridge_units_leave(bank):
    assert bank.transfer_all("ward", "lab") == 7
    assert bank.get_units("lab", "O-") == 5


def test_capacity_lets_an_empty_fridge_transfer_into_a_full_one(bank):
    bank.store("ward", "O-", 3)  # ward is full
    assert bank.transfer_all("theatre", "ward") == 0
    assert bank.get_units("ward", "O-") == 8


# --- retire_fridge --------------------------------------------------------------


def test_capacity_allows_a_retire_that_fits(bank):
    bank.store("theatre", "O+", 2)
    assert bank.retire_fridge("theatre", "ward") == 2
    assert bank.get_fridges() == ["ward", "lab"]
    assert bank.get_units("ward", "O+") == 2


def test_capacity_stops_a_retire_and_keeps_the_fridge(bank):
    before = state(bank)
    with pytest.raises(FridgeFull):
        bank.retire_fridge("ward", "theatre")
    assert state(bank) == before
    assert bank.get_fridges() == ["ward", "lab", "theatre"]
    assert bank.get_units("ward", "O-") == 5


def test_capacity_lets_a_refused_retire_work_once_there_is_room(bank):
    bank.store("lab", "B+", 2)  # 6 units, and theatre takes 5
    with pytest.raises(FridgeFull):
        bank.retire_fridge("lab", "theatre")
    bank.take("lab", "B+", 1)
    assert bank.retire_fridge("lab", "theatre") == 5
    assert bank.get_fridges() == ["ward", "theatre"]


def test_capacity_of_a_retired_fridge_does_not_matter(bank):
    bank.store("ward", "O-", 3)  # ward is full
    assert bank.retire_fridge("ward", "lab") == 10
    assert bank.get_units("lab", "O-") == 8
