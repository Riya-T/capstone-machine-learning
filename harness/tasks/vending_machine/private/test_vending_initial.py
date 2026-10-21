"""Hidden tests for the initial vending_machine spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with vending.py importable, e.g. in the sandbox):
    python -m pytest private/test_vending_initial.py
"""

import pytest
from vending import NotEnoughCredit, SoldOut, VendingError, VendingMachine

BAD_INTS = [0, -5, 1.5, "10", None]


@pytest.fixture
def machine():
    vm = VendingMachine()
    vm.add_slot("A1", 150)
    vm.add_slot("B2", 100)
    return vm


def state(vm):
    """Every stock count and the credit, to check that a failed call changed nothing."""
    return ({s: vm.get_stock(s) for s in vm.get_slots()}, vm.get_credit())


# --- slots ------------------------------------------------------------------


def test_a_new_slot_is_empty(machine):
    assert machine.get_stock("A1") == 0
    assert machine.get_stock("B2") == 0
    assert machine.get_credit() == 0


def test_slots_are_listed_in_the_order_added():
    vm = VendingMachine()
    for slot_id in ["C3", "A1", "B2"]:
        vm.add_slot(slot_id, 100)
    assert vm.get_slots() == ["C3", "A1", "B2"]


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_slot_ids_are_rejected(bad_id):
    vm = VendingMachine()
    with pytest.raises(ValueError):
        vm.add_slot(bad_id, 100)
    assert vm.get_slots() == []


@pytest.mark.parametrize("price", BAD_INTS)
def test_invalid_prices_are_rejected(price):
    vm = VendingMachine()
    with pytest.raises(ValueError):
        vm.add_slot("A1", price)
    assert vm.get_slots() == []


def test_adding_an_existing_slot_is_rejected(machine):
    machine.restock("A1", 4)
    with pytest.raises(VendingError):
        machine.add_slot("A1", 200)
    assert machine.get_stock("A1") == 4
    assert machine.get_slots() == ["A1", "B2"]


def test_a_bad_price_is_reported_before_an_existing_slot(machine):
    with pytest.raises(ValueError):
        machine.add_slot("A1", 0)


@pytest.mark.parametrize(
    "call",
    [
        lambda vm: vm.restock("Z9", 1),
        lambda vm: vm.buy("Z9"),
        lambda vm: vm.get_stock("Z9"),
        lambda vm: vm.get_stock(None),
        lambda vm: vm.buy(1),
    ],
)
def test_slots_that_do_not_exist_raise_key_error(machine, call):
    machine.restock("A1", 2)
    machine.insert_coins(300)
    before = state(machine)
    with pytest.raises(KeyError):
        call(machine)
    assert state(machine) == before


def test_restocking_adds_up(machine):
    machine.restock("A1", 5)
    machine.restock("A1", 2)
    machine.restock("B2", 1)
    assert machine.get_stock("A1") == 7
    assert machine.get_stock("B2") == 1


@pytest.mark.parametrize("count", BAD_INTS)
def test_invalid_counts_are_rejected(machine, count):
    machine.restock("A1", 3)
    before = state(machine)
    with pytest.raises(ValueError):
        machine.restock("A1", count)
    assert state(machine) == before


def test_a_missing_slot_is_reported_before_a_bad_count(machine):
    with pytest.raises(KeyError):
        machine.restock("Z9", -1)


# --- coins ------------------------------------------------------------------


def test_inserted_coins_add_up(machine):
    machine.insert_coins(100)
    machine.insert_coins(25)
    machine.insert_coins(5)
    assert machine.get_credit() == 130


@pytest.mark.parametrize("amount", BAD_INTS)
def test_invalid_coin_amounts_are_rejected(machine, amount):
    machine.insert_coins(50)
    before = state(machine)
    with pytest.raises(ValueError):
        machine.insert_coins(amount)
    assert state(machine) == before


def test_take_change_returns_the_credit_and_clears_it(machine):
    machine.insert_coins(175)
    assert machine.take_change() == 175
    assert machine.get_credit() == 0
    assert machine.take_change() == 0


def test_take_change_with_no_credit_returns_zero(machine):
    assert machine.take_change() == 0
    assert machine.get_credit() == 0


def test_coins_inserted_after_taking_change_start_fresh(machine):
    machine.insert_coins(100)
    machine.take_change()
    machine.insert_coins(30)
    assert machine.get_credit() == 30


# --- buying -----------------------------------------------------------------


def test_buying_takes_one_item_and_the_price(machine):
    machine.restock("A1", 3)
    machine.insert_coins(400)
    machine.buy("A1")
    assert machine.get_stock("A1") == 2
    assert machine.get_credit() == 250
    machine.buy("A1")
    assert machine.get_stock("A1") == 1
    assert machine.get_credit() == 100


def test_exact_credit_can_be_spent(machine):
    machine.restock("B2", 1)
    machine.insert_coins(100)
    machine.buy("B2")
    assert machine.get_credit() == 0
    assert machine.get_stock("B2") == 0


def test_the_remaining_credit_can_buy_from_another_slot(machine):
    machine.restock("A1", 1)
    machine.restock("B2", 1)
    machine.insert_coins(250)
    machine.buy("A1")
    machine.buy("B2")
    assert machine.get_credit() == 0
    assert machine.take_change() == 0


def test_an_empty_slot_raises_and_changes_nothing(machine):
    machine.restock("B2", 2)
    machine.insert_coins(1000)
    before = state(machine)
    with pytest.raises(SoldOut):
        machine.buy("A1")
    assert state(machine) == before


def test_a_slot_bought_empty_is_sold_out(machine):
    machine.restock("A1", 2)
    machine.insert_coins(1000)
    machine.buy("A1")
    machine.buy("A1")
    with pytest.raises(SoldOut):
        machine.buy("A1")
    assert machine.get_credit() == 700


def test_too_little_credit_raises_and_changes_nothing(machine):
    machine.restock("A1", 2)
    machine.insert_coins(149)
    before = state(machine)
    with pytest.raises(NotEnoughCredit):
        machine.buy("A1")
    assert state(machine) == before


def test_no_credit_at_all_raises_not_enough_credit(machine):
    machine.restock("B2", 1)
    with pytest.raises(NotEnoughCredit):
        machine.buy("B2")
    assert machine.get_stock("B2") == 1


def test_sold_out_is_reported_before_too_little_credit(machine):
    # A1 is empty and the credit is too small for it: SoldOut wins.
    machine.insert_coins(10)
    with pytest.raises(SoldOut):
        machine.buy("A1")
    # With no credit at all the empty slot is still the first problem.
    machine.take_change()
    with pytest.raises(SoldOut):
        machine.buy("B2")


def test_a_missing_slot_is_reported_before_sold_out(machine):
    with pytest.raises(KeyError):
        machine.buy("Z9")


def test_failed_calls_change_nothing(machine):
    machine.restock("A1", 1)
    machine.insert_coins(100)
    for call in (
        lambda: machine.buy("A1"),
        lambda: machine.buy("B2"),
        lambda: machine.restock("A1", 0),
        lambda: machine.insert_coins(-1),
        lambda: machine.add_slot("A1", 10),
    ):
        with pytest.raises((ValueError, VendingError)):
            call()
    assert state(machine) == ({"A1": 1, "B2": 0}, 100)


def test_errors_are_vending_errors():
    assert issubclass(SoldOut, VendingError)
    assert issubclass(NotEnoughCredit, VendingError)
    assert not issubclass(SoldOut, NotEnoughCredit)
    assert not issubclass(NotEnoughCredit, SoldOut)


def test_machines_do_not_share_state():
    first, second = VendingMachine(), VendingMachine()
    first.add_slot("A1", 100)
    first.restock("A1", 3)
    first.insert_coins(50)
    assert second.get_slots() == []
    assert second.get_credit() == 0
    second.add_slot("A1", 100)
    assert second.get_stock("A1") == 0
