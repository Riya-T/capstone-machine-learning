"""Public checks for blood_bank.py.

Usage (with blood_bank.py importable, e.g. in the sandbox):
    python -m pytest public/test_bank_public.py
"""

import pytest
from blood_bank import BloodBank, NotEnoughUnits


@pytest.fixture
def bank():
    b = BloodBank()
    b.add_fridge("ward")
    b.add_fridge("lab")
    return b


def test_store_and_take_change_the_units(bank):
    bank.store("ward", "O-", 5)
    bank.store("ward", "O-", 2)
    bank.take("ward", "O-", 3)
    assert bank.get_units("ward", "O-") == 4
    assert bank.get_units("ward", "A+") == 0


def test_taking_more_than_there_are_raises(bank):
    bank.store("ward", "O-", 5)
    with pytest.raises(NotEnoughUnits):
        bank.take("ward", "O-", 6)
    assert bank.get_units("ward", "O-") == 5


def test_blood_types_are_listed_alphabetically(bank):
    bank.store("ward", "O-", 5)
    bank.store("ward", "AB+", 1)
    bank.store("ward", "A+", 2)
    assert bank.get_blood_types("ward") == ["A+", "AB+", "O-"]
    assert bank.get_blood_types("lab") == []


def test_transfer_all_moves_every_blood_type_and_returns_how_many(bank):
    bank.store("ward", "O-", 5)
    bank.store("ward", "A+", 2)
    bank.store("lab", "B+", 1)
    assert bank.transfer_all("ward", "lab") == 7
    assert bank.get_units("ward", "O-") == 0
    assert bank.get_units("ward", "A+") == 0
    assert bank.get_blood_types("lab") == ["A+", "B+", "O-"]
    assert bank.get_units("lab", "O-") == 5
    assert bank.get_fridges() == ["ward", "lab"]


def test_a_retired_fridge_is_gone(bank):
    bank.store("ward", "O-", 5)
    bank.store("lab", "O-", 1)
    assert bank.retire_fridge("ward", "lab") == 5
    assert bank.get_fridges() == ["lab"]
    assert bank.get_units("lab", "O-") == 6
    with pytest.raises(KeyError):
        bank.get_units("ward", "O-")
    with pytest.raises(KeyError):
        bank.store("ward", "O-", 1)


def test_retiring_an_empty_fridge_returns_0(bank):
    assert bank.retire_fridge("lab", "ward") == 0
    assert bank.get_fridges() == ["ward"]
