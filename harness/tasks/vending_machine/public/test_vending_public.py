"""Public checks for vending.py.

Usage (with vending.py importable, e.g. in the sandbox):
    python -m pytest public/test_vending_public.py
"""

import pytest
from vending import NotEnoughCredit, SoldOut, VendingMachine


@pytest.fixture
def machine():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.add_slot("B2", 100)
    return vm


def test_restocking_adds_items(machine):
    assert machine.get_stock("A1") == 0
    machine.restock("A1", 5)
    machine.restock("A1", 3)
    assert machine.get_stock("A1") == 8
    assert machine.get_slots() == ["A1", "B2"]


def test_buying_takes_an_item_and_the_price(machine):
    machine.restock("A1", 2)
    machine.insert_coins(200)
    machine.buy("A1")
    assert machine.get_stock("A1") == 1
    assert machine.get_credit() == 50


def test_too_little_credit_raises(machine):
    machine.restock("B2", 1)
    machine.insert_coins(60)
    with pytest.raises(NotEnoughCredit):
        machine.buy("B2")
    assert machine.get_stock("B2") == 1
    assert machine.get_credit() == 60


def test_an_empty_slot_raises(machine):
    machine.insert_coins(500)
    with pytest.raises(SoldOut):
        machine.buy("A1")
    assert machine.get_credit() == 500


def test_take_change_returns_the_credit(machine):
    machine.insert_coins(100)
    machine.insert_coins(25)
    assert machine.take_change() == 125


def test_unknown_slot_raises_key_error(machine):
    with pytest.raises(KeyError):
        machine.get_stock("Z9")
    with pytest.raises(ValueError):
        machine.insert_coins(0)
