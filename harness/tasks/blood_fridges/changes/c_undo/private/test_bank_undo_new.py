"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with blood_bank.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_bank_undo_new.py
"""

import pytest
from blood_bank import BloodBank, BloodBankError, NotEnoughUnits


@pytest.fixture
def bank():
    b = BloodBank()
    for name in ["ward", "lab", "theatre"]:
        b.add_fridge(name)
    b.store("ward", "O-", 3)
    b.store("ward", "A+", 2)
    b.store("lab", "B+", 4)
    return b


def held(b, fridge):
    """The blood types the fridge holds units of, with their units. Blood
    types listed with 0 units are left out: listing them is unspecified."""
    return [(t, b.get_units(fridge, t)) for t in b.get_blood_types(fridge) if b.get_units(fridge, t)]


def state(b):
    return [(f, held(b, f)) for f in b.get_fridges()]


# --- each call can be undone ------------------------------------------------


def test_undo_of_storing_a_new_blood_type(bank):
    before = state(bank)
    bank.store("theatre", "AB-", 2)
    bank.undo()
    assert state(bank) == before
    assert held(bank, "theatre") == []


def test_undo_of_storing_more_of_a_blood_type(bank):
    bank.store("ward", "O-", 5)
    bank.undo()
    assert bank.get_units("ward", "O-") == 3


def test_undo_of_taking_every_unit_of_a_blood_type(bank):
    before = state(bank)
    bank.take("ward", "A+", 2)
    bank.undo()
    assert state(bank) == before
    assert bank.get_blood_types("ward") == ["A+", "O-"]


def test_undo_of_transfer_all_restores_both_fridges_at_once(bank):
    before = state(bank)
    assert bank.transfer_all("ward", "lab") == 5
    bank.undo()
    assert state(bank) == before
    assert held(bank, "lab") == [("B+", 4)]


def test_undo_of_transfer_all_into_an_empty_fridge(bank):
    before = state(bank)
    bank.transfer_all("lab", "theatre")
    bank.undo()
    assert state(bank) == before
    assert held(bank, "theatre") == []


def test_undo_of_retire_fridge_brings_it_back_with_its_units(bank):
    before = state(bank)
    assert bank.retire_fridge("ward", "theatre") == 5
    bank.undo()
    assert state(bank) == before
    assert bank.get_fridges() == ["ward", "lab", "theatre"]
    assert bank.get_units("theatre", "O-") == 0


def test_undo_of_retire_fridge_keeps_its_place_in_the_list(bank):
    bank.add_fridge("cellar")
    before = state(bank)
    bank.retire_fridge("lab", "cellar")
    assert bank.get_fridges() == ["ward", "theatre", "cellar"]
    bank.undo()
    assert bank.get_fridges() == ["ward", "lab", "theatre", "cellar"]
    assert state(bank) == before


def test_undo_makes_a_retired_fridge_usable_again(bank):
    bank.retire_fridge("ward", "theatre")
    bank.undo()
    bank.store("ward", "O-", 1)
    assert bank.get_units("ward", "O-") == 4
    with pytest.raises(BloodBankError):
        bank.add_fridge("ward")
    assert bank.retire_fridge("ward", "lab") == 6
    assert bank.get_fridges() == ["lab", "theatre"]


def test_undo_of_add_fridge_removes_it_and_frees_the_name(bank):
    bank.add_fridge("cellar")
    bank.undo()
    assert bank.get_fridges() == ["ward", "lab", "theatre"]
    with pytest.raises(KeyError):
        bank.get_blood_types("cellar")
    bank.add_fridge("cellar")
    assert bank.get_fridges() == ["ward", "lab", "theatre", "cellar"]
    assert bank.get_blood_types("cellar") == []


# --- calls that move nothing ------------------------------------------------


def test_undo_of_a_transfer_all_that_moved_nothing(bank):
    bank.store("theatre", "AB-", 1)
    bank.take("theatre", "AB-", 1)
    assert bank.transfer_all("theatre", "ward") == 0
    bank.undo()  # the transfer_all, which changed nothing
    assert held(bank, "theatre") == []
    bank.undo()  # the take
    assert bank.get_units("theatre", "AB-") == 1


def test_undo_of_retiring_an_empty_fridge(bank):
    bank.store("lab", "B+", 1)
    assert bank.retire_fridge("theatre", "lab") == 0
    bank.undo()
    assert bank.get_fridges() == ["ward", "lab", "theatre"]
    assert bank.get_units("lab", "B+") == 5
    bank.undo()
    assert bank.get_units("lab", "B+") == 4


# --- what is and is not recorded --------------------------------------------


def test_undo_steps_back_one_call_at_a_time():
    b = BloodBank()
    calls = [
        lambda: b.add_fridge("ward"),
        lambda: b.add_fridge("lab"),
        lambda: b.store("ward", "O-", 5),
        lambda: b.store("ward", "A+", 2),
        lambda: b.add_fridge("theatre"),
        lambda: b.store("lab", "B+", 4),
        lambda: b.take("ward", "O-", 1),
        lambda: b.transfer_all("lab", "theatre"),
        lambda: b.retire_fridge("ward", "theatre"),
        lambda: b.add_fridge("cellar"),
        lambda: b.store("cellar", "AB-", 1),
        lambda: b.transfer_all("theatre", "cellar"),
        lambda: b.retire_fridge("cellar", "theatre"),
    ]
    states = [state(b)]
    for call in calls:
        call()
        states.append(state(b))
    assert b.get_fridges() == ["lab", "theatre"]
    assert b.get_units("theatre", "O-") == 4
    assert b.get_units("theatre", "AB-") == 1
    for expected in reversed(states[:-1]):
        b.undo()
        assert state(b) == expected
    with pytest.raises(BloodBankError):
        b.undo()
    assert b.get_fridges() == []


def test_undo_skips_calls_that_raised(bank):
    bank.store("theatre", "AB-", 2)
    for call in (
        lambda: bank.take("ward", "O-", 99),
        lambda: bank.take("ward", "AB-", 1),
        lambda: bank.transfer_all("ward", "ward"),
        lambda: bank.transfer_all("ward", "cellar"),
        lambda: bank.retire_fridge("lab", "lab"),
        lambda: bank.retire_fridge("cellar", "lab"),
        lambda: bank.add_fridge("ward"),
        lambda: bank.store("cellar", "O-", 1),
        lambda: bank.store("ward", "O-", 0),
    ):
        with pytest.raises((ValueError, KeyError, BloodBankError)):
            call()
    bank.undo()  # the AB- stored in theatre
    assert held(bank, "theatre") == []
    assert bank.get_units("ward", "O-") == 3


def test_undo_ignores_get_calls(bank):
    bank.store("theatre", "AB-", 2)
    bank.get_units("theatre", "AB-")
    bank.get_blood_types("theatre")
    bank.get_fridges()
    bank.undo()
    assert held(bank, "theatre") == []
    assert bank.get_units("lab", "B+") == 4


def test_undo_has_no_redo():
    b = BloodBank()
    b.add_fridge("ward")
    b.store("ward", "O-", 3)
    b.undo()
    b.undo()
    assert b.get_fridges() == []
    with pytest.raises(BloodBankError):
        b.undo()


def test_undo_after_new_calls_takes_back_the_new_calls_first(bank):
    bank.store("theatre", "AB-", 2)
    bank.undo()
    bank.store("theatre", "O+", 1)
    bank.undo()
    assert held(bank, "theatre") == []
    bank.undo()  # the B+ stored in lab by the fixture
    assert held(bank, "lab") == []
    assert bank.get_blood_types("ward") == ["A+", "O-"]


def test_undo_with_nothing_left_raises_and_changes_nothing():
    b = BloodBank()
    with pytest.raises(BloodBankError):
        b.undo()
    b.add_fridge("ward")
    b.undo()
    with pytest.raises(BloodBankError):
        b.undo()
    assert b.get_fridges() == []
    b.add_fridge("ward")
    b.store("ward", "O-", 1)
    assert b.get_units("ward", "O-") == 1


def test_undo_of_the_whole_fixture(bank):
    for _ in range(6):
        bank.undo()
    assert bank.get_fridges() == []
    with pytest.raises(BloodBankError):
        bank.undo()


def test_undo_restores_units_that_later_calls_check(bank):
    bank.take("ward", "O-", 3)
    bank.undo()
    bank.transfer_all("ward", "lab")
    assert bank.get_units("lab", "O-") == 3
    with pytest.raises(NotEnoughUnits):
        bank.take("ward", "O-", 1)
    bank.undo()
    bank.take("ward", "O-", 3)
    assert held(bank, "ward") == [("A+", 2)]
