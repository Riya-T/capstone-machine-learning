"""Public checks for the c_capacity change (slot capacities). Shown to the
editor, never to the writer.

Usage (with vending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

import pytest
from vending import SlotFull, VendingMachine


def test_restocking_past_the_capacity_raises():
    vm = VendingMachine()
    vm.add_slot("A1", 150, capacity=5)
    vm.restock("A1", 3)
    with pytest.raises(SlotFull):
        vm.restock("A1", 3)
    assert vm.get_stock("A1") == 3
    assert vm.get_capacity("A1") == 5


def test_slots_without_a_capacity_have_no_limit():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.restock("A1", 10**6)
    assert vm.get_capacity("A1") is None


def test_set_capacity_replaces_the_limit():
    vm = VendingMachine()
    vm.add_slot("A1", 150, capacity=2)
    vm.set_capacity("A1", 4)
    vm.restock("A1", 4)
    assert vm.get_stock("A1") == 4
