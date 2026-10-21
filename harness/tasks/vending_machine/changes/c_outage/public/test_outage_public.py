"""Public checks for the c_outage change (slots out of order). Shown to the
editor, never to the writer.

Usage (with vending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_outage/public/test_outage_public.py
"""

import pytest
from vending import SlotDisabled, VendingMachine


def test_a_disabled_slot_cannot_be_bought_from():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.restock("A1", 2)
    vm.insert_coins(300)
    vm.disable_slot("A1")
    assert vm.is_disabled("A1")
    with pytest.raises(SlotDisabled):
        vm.buy("A1")
    assert vm.get_stock("A1") == 2
    assert vm.get_credit() == 300
    vm.enable_slot("A1")
    vm.buy("A1")
    assert vm.get_stock("A1") == 1


def test_working_slots_leave_out_disabled_ones():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.add_slot("B2", 100)
    vm.add_slot("C3", 200)
    vm.disable_slot("B2")
    assert vm.get_working_slots() == ["A1", "C3"]
    assert vm.get_slots() == ["A1", "B2", "C3"]


def test_restocking_a_disabled_slot_still_works():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.disable_slot("A1")
    vm.restock("A1", 4)
    assert vm.get_stock("A1") == 4
