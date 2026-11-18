"""Hidden tests for the initial blood_fridges spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with blood_bank.py importable, e.g. in the sandbox):
    python -m pytest private/test_bank_initial.py
"""

import pytest
from blood_bank import BloodBank, BloodBankError, NotEnoughUnits

BAD_COUNTS = [0, -3]


@pytest.fixture
def bank():
    b = BloodBank()
    for name in ["ward", "lab", "theatre"]:
        b.add_fridge(name)
    b.store("ward", "O-", 5)
    b.store("ward", "A+", 2)
    return b


def state(b):
    """Every fridge in order with the blood types it holds units of, to check
    that a failed call changed nothing. Blood types listed with 0 units are
    left out, since listing them is unspecified."""
    return [
        (f, [(t, b.get_units(f, t)) for t in b.get_blood_types(f) if b.get_units(f, t)])
        for f in b.get_fridges()
    ]


# --- fridges ----------------------------------------------------------------


def test_a_new_fridge_is_empty():
    b = BloodBank()
    b.add_fridge("ward")
    assert b.get_blood_types("ward") == []
    assert b.get_units("ward", "O-") == 0


def test_fridges_are_listed_in_the_order_added():
    b = BloodBank()
    for name in ["theatre", "ward", "lab"]:
        b.add_fridge(name)
    assert b.get_fridges() == ["theatre", "ward", "lab"]


def test_adding_a_name_in_use_is_rejected(bank):
    before = state(bank)
    with pytest.raises(BloodBankError):
        bank.add_fridge("ward")
    assert state(bank) == before


UNKNOWN_FRIDGE_CALLS = [
    lambda b, x: b.store(x, "O-", 1),
    lambda b, x: b.take(x, "O-", 1),
    lambda b, x: b.transfer_all(x, "lab"),
    lambda b, x: b.transfer_all("ward", x),
    lambda b, x: b.retire_fridge(x, "lab"),
    lambda b, x: b.retire_fridge("ward", x),
    lambda b, x: b.get_units(x, "O-"),
    lambda b, x: b.get_blood_types(x),
]


@pytest.mark.parametrize("call", UNKNOWN_FRIDGE_CALLS)
def test_fridges_that_were_never_added_raise_key_error(bank, call):
    before = state(bank)
    with pytest.raises(KeyError):
        call(bank, "cellar")
    assert state(bank) == before


@pytest.mark.parametrize("call", UNKNOWN_FRIDGE_CALLS)
def test_a_retired_fridge_is_not_in_use(bank, call):
    bank.retire_fridge("theatre", "lab")  # theatre is empty
    before = state(bank)
    with pytest.raises(KeyError):
        call(bank, "theatre")
    assert state(bank) == before


# --- storing and taking -------------------------------------------------------


def test_store_and_take_change_only_their_own_fridge_and_type(bank):
    bank.store("ward", "O-", 3)
    bank.take("ward", "O-", 6)
    bank.store("lab", "O-", 1)
    assert bank.get_units("ward", "O-") == 2
    assert bank.get_units("lab", "O-") == 1
    assert bank.get_units("ward", "A+") == 2
    assert bank.get_units("theatre", "O-") == 0


def test_every_unit_of_a_blood_type_can_be_taken(bank):
    bank.take("ward", "A+", 2)
    assert bank.get_units("ward", "A+") == 0
    assert bank.get_units("ward", "O-") == 5
    with pytest.raises(NotEnoughUnits):
        bank.take("ward", "A+", 1)


def test_blood_types_of_each_fridge_are_alphabetical(bank):
    bank.store("lab", "O+", 1)
    bank.store("lab", "AB-", 2)
    bank.store("lab", "B+", 3)
    assert bank.get_blood_types("lab") == ["AB-", "B+", "O+"]
    assert bank.get_blood_types("ward") == ["A+", "O-"]


def test_taking_more_than_there_are_raises_and_changes_nothing(bank):
    before = state(bank)
    with pytest.raises(NotEnoughUnits):
        bank.take("ward", "A+", 3)
    with pytest.raises(NotEnoughUnits):
        bank.take("ward", "B+", 1)
    with pytest.raises(NotEnoughUnits):
        bank.take("lab", "O-", 1)
    assert state(bank) == before


@pytest.mark.parametrize("count", BAD_COUNTS)
@pytest.mark.parametrize(
    "call",
    [lambda b, c: b.store("ward", "O-", c), lambda b, c: b.take("ward", "O-", c)],
    ids=["store", "take"],
)
def test_counts_of_0_or_less_are_rejected(bank, call, count):
    before = state(bank)
    with pytest.raises(ValueError):
        call(bank, count)
    assert state(bank) == before


# --- transfer_all -------------------------------------------------------------


def test_transfer_all_adds_to_what_the_other_fridge_holds(bank):
    bank.store("lab", "O-", 1)
    bank.store("lab", "B-", 4)
    assert bank.transfer_all("ward", "lab") == 7
    assert bank.get_units("ward", "O-") == 0
    assert bank.get_units("ward", "A+") == 0
    assert bank.get_blood_types("lab") == ["A+", "B-", "O-"]
    assert bank.get_units("lab", "O-") == 6
    assert bank.get_units("lab", "A+") == 2
    assert bank.get_fridges() == ["ward", "lab", "theatre"]


def test_a_fridge_emptied_by_transfer_all_can_be_used_again(bank):
    bank.transfer_all("ward", "theatre")
    bank.store("ward", "O-", 1)
    assert bank.get_units("ward", "O-") == 1
    assert bank.transfer_all("theatre", "ward") == 7
    assert bank.get_units("ward", "O-") == 6


def test_transfer_all_from_an_empty_fridge_moves_nothing(bank):
    before = state(bank)
    assert bank.transfer_all("theatre", "ward") == 0
    assert state(bank) == before


# --- retire_fridge ------------------------------------------------------------


def test_retire_fridge_moves_every_unit_and_removes_the_fridge(bank):
    bank.store("theatre", "O-", 2)
    assert bank.retire_fridge("ward", "theatre") == 7
    assert bank.get_fridges() == ["lab", "theatre"]
    assert bank.get_units("theatre", "O-") == 7
    assert bank.get_units("theatre", "A+") == 2


def test_retiring_an_empty_fridge_moves_nothing(bank):
    assert bank.retire_fridge("lab", "ward") == 0
    assert bank.get_fridges() == ["ward", "theatre"]
    assert bank.get_units("ward", "O-") == 5


def test_the_other_fridges_keep_their_order_after_a_retire(bank):
    bank.add_fridge("cellar")
    bank.retire_fridge("lab", "cellar")
    assert bank.get_fridges() == ["ward", "theatre", "cellar"]


def test_units_moved_by_a_retire_can_be_taken_from_their_new_fridge(bank):
    bank.retire_fridge("ward", "lab")
    bank.take("lab", "O-", 5)
    assert bank.get_units("lab", "O-") == 0
    assert bank.get_units("lab", "A+") == 2


@pytest.mark.parametrize(
    "call",
    [
        lambda b: b.transfer_all("ward", "ward"),
        lambda b: b.retire_fridge("ward", "ward"),
        lambda b: b.transfer_all("theatre", "theatre"),
    ],
    ids=["transfer_all", "retire_fridge", "transfer_all_empty"],
)
def test_the_same_fridge_on_both_sides_is_rejected(bank, call):
    before = state(bank)
    with pytest.raises(ValueError):
        call(bank)
    assert state(bank) == before


# --- general --------------------------------------------------------------------


def test_not_enough_units_is_a_blood_bank_error():
    assert issubclass(NotEnoughUnits, BloodBankError)


def test_banks_do_not_share_fridges():
    first, second = BloodBank(), BloodBank()
    first.add_fridge("ward")
    first.store("ward", "O-", 3)
    assert second.get_fridges() == []
    second.add_fridge("ward")
    assert second.get_units("ward", "O-") == 0
