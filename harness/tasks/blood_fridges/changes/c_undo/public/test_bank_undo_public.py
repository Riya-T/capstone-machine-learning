"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with blood_bank.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_bank_undo_public.py
"""

import pytest
from blood_bank import BloodBank, BloodBankError


@pytest.fixture
def bank():
    b = BloodBank()
    b.add_fridge("ward")
    b.add_fridge("lab")
    return b


def test_undo_takes_back_the_last_store(bank):
    bank.store("ward", "O-", 5)
    bank.store("ward", "O-", 2)
    bank.undo()
    assert bank.get_units("ward", "O-") == 5
    bank.undo()
    assert bank.get_units("ward", "O-") == 0


def test_undo_takes_back_a_take(bank):
    bank.store("lab", "A+", 4)
    bank.take("lab", "A+", 3)
    bank.undo()
    assert bank.get_units("lab", "A+") == 4


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(BloodBankError):
        BloodBank().undo()
