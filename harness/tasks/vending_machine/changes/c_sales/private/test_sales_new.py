"""Hidden tests for the c_sales change (sales reporting). Never shown to the
writer or the editor.

Usage (with vending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_sales/private/test_sales_new.py
"""

import pytest
from vending import NotEnoughCredit, SoldOut, VendingMachine


@pytest.fixture
def machine():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.add_slot("B2", 100)
    vm.add_slot("C3", 250)
    vm.restock("A1", 3)
    vm.restock("B2", 3)
    vm.restock("C3", 3)
    return vm


def test_a_new_machine_reports_nothing_sold(machine):
    assert machine.get_revenue() == 0
    assert machine.get_sales("A1") == 0
    assert machine.get_sales_report() == [("A1", 0), ("B2", 0), ("C3", 0)]


def test_restocking_does_not_count_as_sales(machine):
    machine.restock("A1", 10)
    assert machine.get_sales("A1") == 0
    assert machine.get_revenue() == 0


def test_each_purchase_counts_once(machine):
    machine.insert_coins(1000)
    machine.buy("A1")
    machine.buy("B2")
    machine.buy("B2")
    assert machine.get_sales("A1") == 1
    assert machine.get_sales("B2") == 2
    assert machine.get_sales("C3") == 0


def test_revenue_adds_each_slot_price(machine):
    machine.insert_coins(1000)
    machine.buy("A1")
    machine.buy("C3")
    machine.buy("B2")
    assert machine.get_revenue() == 500


def test_unspent_coins_and_change_are_not_revenue(machine):
    machine.insert_coins(500)
    machine.buy("B2")
    assert machine.get_revenue() == 100
    assert machine.take_change() == 400
    assert machine.get_revenue() == 100
    machine.insert_coins(75)
    assert machine.get_revenue() == 100


def test_failed_purchases_do_not_count(machine):
    machine.insert_coins(100)
    machine.buy("B2")
    with pytest.raises(NotEnoughCredit):
        machine.buy("A1")
    machine.insert_coins(1000)
    machine.buy("B2")
    machine.buy("B2")
    with pytest.raises(SoldOut):
        machine.buy("B2")
    with pytest.raises(KeyError):
        machine.buy("Z9")
    assert machine.get_sales("B2") == 3
    assert machine.get_sales("A1") == 0
    assert machine.get_revenue() == 300


def test_get_sales_raises_key_error_for_unknown_slots(machine):
    with pytest.raises(KeyError):
        machine.get_sales("Z9")
    with pytest.raises(KeyError):
        machine.get_sales(None)


def test_report_sorts_most_sold_first(machine):
    machine.insert_coins(2000)
    machine.buy("C3")
    machine.buy("C3")
    machine.buy("C3")
    machine.buy("A1")
    machine.buy("B2")
    machine.buy("B2")
    assert machine.get_sales_report() == [("C3", 3), ("B2", 2), ("A1", 1)]


def test_report_ties_keep_the_order_slots_were_added(machine):
    machine.insert_coins(2000)
    machine.buy("C3")
    machine.buy("A1")
    machine.buy("B2")
    assert machine.get_sales_report() == [("A1", 1), ("B2", 1), ("C3", 1)]
    machine.buy("C3")
    machine.buy("A1")
    assert machine.get_sales_report() == [("A1", 2), ("C3", 2), ("B2", 1)]


def test_report_includes_slots_added_later():
    vm = VendingMachine()
    vm.add_slot("A1", 100)
    vm.restock("A1", 1)
    vm.insert_coins(100)
    vm.buy("A1")
    vm.add_slot("B2", 100)
    assert vm.get_sales_report() == [("A1", 1), ("B2", 0)]
    assert vm.get_sales("B2") == 0


def test_sales_survive_selling_out_and_restocking(machine):
    machine.insert_coins(1000)
    for _ in range(3):
        machine.buy("B2")
    with pytest.raises(SoldOut):
        machine.buy("B2")
    machine.restock("B2", 1)
    machine.buy("B2")
    assert machine.get_sales("B2") == 4
    assert machine.get_stock("B2") == 0
    assert machine.get_revenue() == 400
