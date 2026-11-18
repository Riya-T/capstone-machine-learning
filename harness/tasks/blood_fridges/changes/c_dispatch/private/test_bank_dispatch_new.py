"""Hidden tests for the c_dispatch change (orders taken as a whole). Never
shown to the writer or the editor.

Usage (with blood_bank.py importable, e.g. in the sandbox):
    python -m pytest changes/c_dispatch/private/test_bank_dispatch_new.py
"""

import pytest
from blood_bank import BloodBank, NotEnoughUnits


@pytest.fixture
def bank():
    b = BloodBank()
    for name in ["ward", "lab", "theatre"]:
        b.add_fridge(name)
    b.store("ward", "O-", 5)
    b.store("ward", "A+", 2)
    b.store("lab", "B+", 4)
    b.store("lab", "O-", 1)
    return b


def held(b, fridge):
    """The blood types the fridge holds units of, with their units. Blood
    types listed with 0 units are left out: listing them is unspecified."""
    return [(t, b.get_units(fridge, t)) for t in b.get_blood_types(fridge) if b.get_units(fridge, t)]


def state(b):
    return [(f, held(b, f)) for f in b.get_fridges()]


# --- orders that go out ---------------------------------------------------------


def test_dispatch_of_a_single_tuple_is_like_take(bank):
    assert bank.dispatch([("ward", "O-", 3)]) == 3
    assert bank.get_units("ward", "O-") == 2
    assert bank.get_units("ward", "A+") == 2


def test_dispatch_from_several_fridges(bank):
    assert bank.dispatch([("lab", "B+", 1), ("ward", "A+", 2), ("lab", "O-", 1)]) == 4
    assert state(bank) == [
        ("ward", [("O-", 5)]),
        ("lab", [("B+", 3)]),
        ("theatre", []),
    ]


def test_dispatch_can_empty_a_fridge(bank):
    assert bank.dispatch([("ward", "O-", 5), ("ward", "A+", 2)]) == 7
    assert held(bank, "ward") == []
    assert bank.get_fridges() == ["ward", "lab", "theatre"]


def test_dispatch_of_the_same_blood_type_twice_takes_both(bank):
    bank.store("ward", "O-", 1)  # 6 units
    assert bank.dispatch([("ward", "O-", 3), ("ward", "O-", 3)]) == 6
    assert bank.get_units("ward", "O-") == 0
    assert held(bank, "ward") == [("A+", 2)]


def test_dispatch_leaves_the_other_fridges_alone(bank):
    bank.dispatch([("lab", "B+", 4)])
    assert bank.get_units("ward", "O-") == 5
    assert bank.get_units("lab", "O-") == 1
    assert bank.get_blood_types("theatre") == []


def test_dispatched_units_are_gone_for_later_calls(bank):
    bank.dispatch([("ward", "O-", 4), ("lab", "O-", 1)])
    with pytest.raises(NotEnoughUnits):
        bank.take("ward", "O-", 2)
    with pytest.raises(NotEnoughUnits):
        bank.take("lab", "O-", 1)
    bank.take("ward", "O-", 1)
    assert held(bank, "ward") == [("A+", 2)]


# --- orders that fail as a whole ------------------------------------------------


def test_dispatch_where_later_tuples_see_earlier_ones(bank):
    before = state(bank)
    with pytest.raises(NotEnoughUnits):
        bank.dispatch([("ward", "O-", 3), ("ward", "O-", 3)])
    assert state(bank) == before


def test_dispatch_with_the_last_tuple_short_changes_nothing(bank):
    before = state(bank)
    with pytest.raises(NotEnoughUnits):
        bank.dispatch([("ward", "O-", 5), ("lab", "B+", 4), ("ward", "A+", 3)])
    assert state(bank) == before


def test_dispatch_of_a_blood_type_the_fridge_lacks_changes_nothing(bank):
    before = state(bank)
    with pytest.raises(NotEnoughUnits):
        bank.dispatch([("ward", "A+", 1), ("theatre", "O-", 1)])
    assert state(bank) == before


def test_dispatch_with_an_unknown_fridge_changes_nothing(bank):
    before = state(bank)
    with pytest.raises(KeyError):
        bank.dispatch([("ward", "O-", 2), ("cellar", "O-", 1)])
    assert state(bank) == before


def test_dispatch_with_a_retired_fridge_changes_nothing(bank):
    bank.retire_fridge("theatre", "lab")
    before = state(bank)
    with pytest.raises(KeyError):
        bank.dispatch([("lab", "B+", 1), ("theatre", "B+", 1)])
    assert state(bank) == before


@pytest.mark.parametrize("count", [0, -2])
def test_dispatch_with_a_bad_count_changes_nothing(bank, count):
    before = state(bank)
    with pytest.raises(ValueError):
        bank.dispatch([("ward", "O-", 1), ("lab", "B+", count)])
    assert state(bank) == before


def test_dispatch_that_failed_can_be_retried_once_fixed(bank):
    with pytest.raises(NotEnoughUnits):
        bank.dispatch([("ward", "A+", 2), ("lab", "O-", 2)])
    bank.store("lab", "O-", 1)
    assert bank.dispatch([("ward", "A+", 2), ("lab", "O-", 2)]) == 4
    assert held(bank, "ward") == [("O-", 5)]
    assert held(bank, "lab") == [("B+", 4)]
