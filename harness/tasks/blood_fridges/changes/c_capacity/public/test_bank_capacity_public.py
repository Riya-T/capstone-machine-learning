"""Public checks for the c_capacity change (fridge capacity). Shown to the
editor, never to the writer.

Usage (with blood_bank.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_bank_capacity_public.py
"""

import pytest
from blood_bank import BloodBank, FridgeFull


@pytest.fixture
def bank():
    b = BloodBank()
    b.add_fridge("ward", capacity=10)
    b.add_fridge("lab")
    return b


def test_capacity_is_reported(bank):
    assert bank.get_capacity("ward") == 10
    assert bank.get_capacity("lab") is None


def test_storing_past_the_capacity_raises(bank):
    bank.store("ward", "O-", 6)
    bank.store("ward", "A+", 4)
    with pytest.raises(FridgeFull):
        bank.store("ward", "O-", 1)
    assert bank.get_units("ward", "O-") == 6
    assert bank.get_units("ward", "A+") == 4
