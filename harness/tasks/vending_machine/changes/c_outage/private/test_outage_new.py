"""Hidden tests for the c_outage change (slots out of order). Never shown to
the writer or the editor.

Usage (with vending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_outage/private/test_outage_new.py
"""

import pytest
from vending import NotEnoughCredit, SlotDisabled, SoldOut, VendingError, VendingMachine


@pytest.fixture
def machine():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.add_slot("B2", 100)
    vm.restock("A1", 3)
    vm.restock("B2", 3)
    return vm


def state(vm):
    return ({s: vm.get_stock(s) for s in vm.get_slots()}, vm.get_credit())


def test_new_slots_are_enabled(machine):
    assert not machine.is_disabled("A1")
    assert not machine.is_disabled("B2")
    assert machine.get_working_slots() == ["A1", "B2"]


def test_disabling_or_enabling_twice_is_harmless(machine):
    machine.disable_slot("A1")
    machine.disable_slot("A1")
    assert machine.is_disabled("A1")
    assert not machine.is_disabled("B2")
    machine.enable_slot("A1")
    machine.enable_slot("A1")
    assert not machine.is_disabled("A1")
    assert machine.get_working_slots() == ["A1", "B2"]


@pytest.mark.parametrize("method", ["disable_slot", "enable_slot", "is_disabled"])
@pytest.mark.parametrize("slot_id", ["Z9", None, 1])
def test_slots_that_do_not_exist_raise_key_error(machine, method, slot_id):
    with pytest.raises(KeyError):
        getattr(machine, method)(slot_id)


def test_buying_from_a_disabled_slot_changes_nothing(machine):
    machine.insert_coins(500)
    machine.disable_slot("A1")
    before = state(machine)
    with pytest.raises(SlotDisabled):
        machine.buy("A1")
    assert state(machine) == before


def test_other_slots_still_sell_while_one_is_disabled(machine):
    machine.insert_coins(500)
    machine.disable_slot("A1")
    machine.buy("B2")
    assert machine.get_stock("B2") == 2
    assert machine.get_credit() == 400


def test_disabled_is_reported_before_sold_out_and_credit(machine):
    machine.add_slot("C3", 200)  # empty
    machine.disable_slot("C3")
    with pytest.raises(SlotDisabled):
        machine.buy("C3")
    machine.disable_slot("A1")  # stocked, but no credit
    with pytest.raises(SlotDisabled):
        machine.buy("A1")


def test_a_missing_slot_is_reported_before_disabled(machine):
    machine.disable_slot("A1")
    with pytest.raises(KeyError):
        machine.buy("Z9")


def test_an_enabled_slot_reports_its_usual_errors(machine):
    machine.disable_slot("A1")
    machine.enable_slot("A1")
    with pytest.raises(NotEnoughCredit):
        machine.buy("A1")
    machine.add_slot("C3", 200)
    machine.disable_slot("C3")
    machine.enable_slot("C3")
    machine.insert_coins(500)
    with pytest.raises(SoldOut):
        machine.buy("C3")


def test_disabled_slots_can_still_be_restocked_and_read(machine):
    machine.disable_slot("A1")
    machine.restock("A1", 2)
    assert machine.get_stock("A1") == 5
    assert machine.get_slots() == ["A1", "B2"]
    with pytest.raises(ValueError):
        machine.restock("A1", 0)


def test_disabling_changes_no_stock_or_credit(machine):
    machine.insert_coins(120)
    before = state(machine)
    machine.disable_slot("A1")
    machine.disable_slot("B2")
    machine.enable_slot("A1")
    assert state(machine) == before


def test_working_slots_keep_the_order_slots_were_added(machine):
    machine.add_slot("C3", 200)
    machine.disable_slot("A1")
    assert machine.get_working_slots() == ["B2", "C3"]
    machine.disable_slot("C3")
    machine.enable_slot("A1")
    assert machine.get_working_slots() == ["A1", "B2"]
    machine.disable_slot("A1")
    machine.disable_slot("B2")
    assert machine.get_working_slots() == []


def test_slot_disabled_is_a_vending_error_but_not_sold_out():
    assert issubclass(SlotDisabled, VendingError)
    assert not issubclass(SlotDisabled, SoldOut)
    assert not issubclass(SlotDisabled, NotEnoughCredit)
