"""Public checks for the c_dispatch change (orders taken as a whole). Shown
to the editor, never to the writer.

Usage (with blood_bank.py importable, e.g. in the sandbox):
    python -m pytest changes/c_dispatch/public/test_bank_dispatch_public.py
"""

import pytest
from blood_bank import BloodBank, NotEnoughUnits


@pytest.fixture
def bank():
    b = BloodBank()
    b.add_fridge("ward")
    b.add_fridge("lab")
    b.store("ward", "O-", 5)
    b.store("lab", "A+", 3)
    return b


def test_dispatch_takes_every_tuple_and_returns_the_total(bank):
    assert bank.dispatch([("ward", "O-", 2), ("lab", "A+", 3)]) == 5
    assert bank.get_units("ward", "O-") == 3
    assert bank.get_units("lab", "A+") == 0


def test_dispatch_with_one_tuple_short_takes_nothing(bank):
    with pytest.raises(NotEnoughUnits):
        bank.dispatch([("ward", "O-", 2), ("lab", "A+", 4)])
    assert bank.get_units("ward", "O-") == 5
    assert bank.get_units("lab", "A+") == 3
