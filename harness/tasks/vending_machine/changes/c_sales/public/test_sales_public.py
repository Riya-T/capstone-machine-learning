"""Public checks for the c_sales change (sales reporting). Shown to the
editor, never to the writer.

Usage (with vending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_sales/public/test_sales_public.py
"""

from vending import VendingMachine


def test_sales_and_revenue_count_items_bought():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.add_slot("B2", 100)
    vm.restock("A1", 5)
    vm.restock("B2", 5)
    vm.insert_coins(1000)
    vm.buy("A1")
    vm.buy("A1")
    vm.buy("B2")
    assert vm.get_sales("A1") == 2
    assert vm.get_sales("B2") == 1
    assert vm.get_revenue() == 400


def test_the_report_lists_the_most_sold_slot_first():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.add_slot("B2", 100)
    vm.add_slot("C3", 200)
    vm.restock("B2", 5)
    vm.insert_coins(1000)
    vm.buy("B2")
    vm.buy("B2")
    assert vm.get_sales_report() == [("B2", 2), ("A1", 0), ("C3", 0)]


def test_a_new_machine_has_sold_nothing():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.insert_coins(300)
    assert vm.get_revenue() == 0
    assert vm.get_sales("A1") == 0
