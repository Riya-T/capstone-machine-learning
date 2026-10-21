"""Hidden tests for the c_capacity change (slot capacities). Never shown to
the writer or the editor.

Usage (with vending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from vending import SlotFull, VendingError, VendingMachine

BAD_CAPACITIES = [0, -1, 1.5, "5", True]


@pytest.fixture
def machine():
    vm = VendingMachine()
    vm.add_slot("A1", 150, capacity=5)
    vm.add_slot("B2", 100)
    return vm


def state(vm):
    return ({s: vm.get_stock(s) for s in vm.get_slots()}, vm.get_credit())


def test_the_default_capacity_is_no_limit(machine):
    assert machine.get_capacity("B2") is None
    machine.restock("B2", 500)
    assert machine.get_stock("B2") == 500


def test_a_slot_can_be_filled_exactly_to_its_capacity(machine):
    machine.restock("A1", 2)
    machine.restock("A1", 3)
    assert machine.get_stock("A1") == 5
    before = state(machine)
    with pytest.raises(SlotFull):
        machine.restock("A1", 1)
    assert state(machine) == before


def test_one_restock_past_the_capacity_adds_nothing(machine):
    before = state(machine)
    with pytest.raises(SlotFull):
        machine.restock("A1", 6)
    assert state(machine) == before


def test_buying_frees_room_for_restocking(machine):
    machine.restock("A1", 5)
    machine.insert_coins(300)
    machine.buy("A1")
    machine.buy("A1")
    machine.restock("A1", 2)
    assert machine.get_stock("A1") == 5


@pytest.mark.parametrize("capacity", BAD_CAPACITIES)
def test_invalid_capacities_are_rejected_when_adding(capacity):
    vm = VendingMachine()
    with pytest.raises(ValueError):
        vm.add_slot("A1", 100, capacity=capacity)
    assert vm.get_slots() == []


def test_a_bad_capacity_is_reported_before_an_existing_slot(machine):
    with pytest.raises(ValueError):
        machine.add_slot("A1", 100, capacity=0)


@pytest.mark.parametrize("method", ["get_capacity", "set_capacity"])
def test_slots_that_do_not_exist_raise_key_error(machine, method):
    args = ("Z9",) if method == "get_capacity" else ("Z9", 3)
    with pytest.raises(KeyError):
        getattr(machine, method)(*args)


def test_set_capacity_can_lower_raise_and_remove_the_limit(machine):
    machine.restock("A1", 3)
    machine.set_capacity("A1", 3)  # equal to the stock is fine
    assert machine.get_capacity("A1") == 3
    with pytest.raises(SlotFull):
        machine.restock("A1", 1)
    machine.set_capacity("A1", 10)
    machine.restock("A1", 7)
    assert machine.get_stock("A1") == 10
    machine.set_capacity("A1", None)
    assert machine.get_capacity("A1") is None
    machine.restock("A1", 1000)
    assert machine.get_stock("A1") == 1010


def test_a_capacity_below_the_stock_is_rejected(machine):
    machine.restock("A1", 4)
    before = state(machine)
    with pytest.raises(VendingError):
        machine.set_capacity("A1", 3)
    assert machine.get_capacity("A1") == 5
    assert state(machine) == before


@pytest.mark.parametrize("capacity", BAD_CAPACITIES)
def test_invalid_capacities_are_rejected_when_setting(machine, capacity):
    with pytest.raises(ValueError):
        machine.set_capacity("A1", capacity)
    assert machine.get_capacity("A1") == 5


def test_a_missing_slot_is_reported_before_a_bad_capacity(machine):
    with pytest.raises(KeyError):
        machine.set_capacity("Z9", -1)


def test_a_bad_capacity_is_reported_before_the_stock_check(machine):
    machine.restock("A1", 4)
    with pytest.raises(ValueError):
        machine.set_capacity("A1", -1)


def test_slot_full_is_checked_after_bad_input(machine):
    machine.restock("A1", 5)
    with pytest.raises(ValueError):
        machine.restock("A1", 0)
    with pytest.raises(KeyError):
        machine.restock("Z9", 100)


def test_slot_full_is_a_vending_error():
    assert issubclass(SlotFull, VendingError)
