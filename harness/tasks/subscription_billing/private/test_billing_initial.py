"""Hidden tests for the initial subscription_billing spec. They decide
whether a program is correct to begin with. Never shown to the writer or the
editor.

Usage (with billing.py importable, e.g. in the sandbox):
    python -m pytest private/test_billing_initial.py
"""

import pytest
from billing import BillingError, BillingSystem

BAD_PRICES = [0, -5]
BAD_NAMES = ["", None]
CUSTOMERS = ["alice", "bob", "carol"]


@pytest.fixture
def billing():
    b = BillingSystem()
    b.add_plan("basic", 900)
    b.add_plan("pro", 1500)
    b.add_plan("lite", 400)
    b.subscribe("alice", "basic")
    b.subscribe("bob", "pro")
    return b


def state(b, customers=("alice", "bob")):
    """Plans and charges of the given customers, to check that a failed call
    changed nothing."""
    return {c: (b.get_plan(c), b.get_charges(c)) for c in customers}


# --- plans ------------------------------------------------------------------


@pytest.mark.parametrize("price", BAD_PRICES)
def test_invalid_prices_are_rejected(price):
    b = BillingSystem()
    with pytest.raises(ValueError):
        b.add_plan("basic", price)
    with pytest.raises(KeyError):
        b.subscribe("alice", "basic")


def test_an_empty_plan_id_is_rejected():
    b = BillingSystem()
    with pytest.raises(ValueError):
        b.add_plan("", 900)


def test_adding_a_plan_twice_is_rejected(billing):
    with pytest.raises(BillingError):
        billing.add_plan("basic", 100)
    # the price was not replaced
    billing.run_cycle()
    assert billing.get_charges("alice") == [900]


# --- customers --------------------------------------------------------------


@pytest.mark.parametrize("customer", BAD_NAMES)
def test_invalid_customers_are_rejected(billing, customer):
    with pytest.raises(ValueError):
        billing.subscribe(customer, "basic")
    assert billing.run_cycle() == 2400


def test_subscribe_errors(billing):
    before = state(billing)
    with pytest.raises(KeyError):
        billing.subscribe("carol", "gold")
    with pytest.raises(BillingError):
        billing.subscribe("alice", "lite")
    assert state(billing) == before
    with pytest.raises(KeyError):
        billing.get_plan("carol")


@pytest.mark.parametrize(
    "call",
    [
        lambda b: b.change_plan("carol", "pro"),
        lambda b: b.change_plan("carol", "gold"),
        lambda b: b.cancel("carol"),
        lambda b: b.get_plan("carol"),
        lambda b: b.get_charges("carol"),
        lambda b: b.get_plan(None),
        lambda b: b.get_charges(1),
    ],
)
def test_customers_who_never_subscribed_raise_key_error(billing, call):
    before = state(billing)
    with pytest.raises(KeyError):
        call(billing)
    assert state(billing) == before


def test_cancelling_stops_the_charges(billing):
    billing.run_cycle()
    billing.cancel("alice")
    assert billing.run_cycle() == 1500
    assert billing.run_cycle() == 1500
    assert billing.get_charges("bob") == [1500, 1500, 1500]


def test_cancelling_after_an_upgrade_stops_the_charges(billing):
    billing.change_plan("alice", "pro")
    billing.cancel("alice")
    assert billing.run_cycle() == 1500


def test_cancelling_changes_no_other_customer(billing):
    billing.run_cycle()
    billing.cancel("bob")
    assert billing.get_plan("alice") == "basic"
    assert billing.get_charges("alice") == [900]
    billing.change_plan("alice", "pro")
    assert billing.get_charges("alice") == [900, 600]


# --- changing plans ---------------------------------------------------------


def test_moving_to_a_cheaper_plan_charges_nothing(billing):
    billing.change_plan("bob", "lite")
    assert billing.get_plan("bob") == "lite"
    assert billing.get_charges("bob") == []
    assert billing.run_cycle() == 1300


def test_moving_to_a_plan_with_the_same_price_charges_nothing(billing):
    billing.add_plan("basic_plus", 900)
    billing.change_plan("alice", "basic_plus")
    assert billing.get_charges("alice") == []


def test_each_upgrade_is_charged(billing):
    billing.change_plan("alice", "lite")
    billing.change_plan("alice", "basic")
    billing.change_plan("alice", "pro")
    assert billing.get_charges("alice") == [500, 600]


def test_charges_mix_cycles_and_upgrades_in_order(billing):
    billing.run_cycle()
    billing.change_plan("alice", "pro")
    billing.run_cycle()
    assert billing.get_charges("alice") == [900, 600, 1500]


def test_moving_to_the_current_plan_is_rejected(billing):
    before = state(billing)
    with pytest.raises(BillingError):
        billing.change_plan("alice", "basic")
    assert state(billing) == before


def test_moving_to_a_plan_that_was_never_added_is_rejected(billing):
    before = state(billing)
    with pytest.raises(KeyError):
        billing.change_plan("alice", "gold")
    assert state(billing) == before


# --- billing cycles ---------------------------------------------------------


def test_a_cycle_with_nobody_subscribed_charges_nothing():
    b = BillingSystem()
    b.add_plan("basic", 900)
    assert b.run_cycle() == 0


def test_every_cycle_charges_again(billing):
    assert billing.run_cycle() == 2400
    assert billing.run_cycle() == 2400
    assert billing.get_charges("alice") == [900, 900]


def test_a_cycle_uses_the_plan_at_that_moment(billing):
    billing.change_plan("bob", "basic")
    assert billing.run_cycle() == 1800
    assert billing.get_charges("bob") == [900]


def test_a_cycle_does_not_count_upgrade_charges(billing):
    billing.change_plan("alice", "pro")
    assert billing.run_cycle() == 3000


def test_systems_do_not_share_state():
    first, second = BillingSystem(), BillingSystem()
    first.add_plan("basic", 900)
    first.subscribe("alice", "basic")
    second.add_plan("basic", 100)
    second.subscribe("alice", "basic")
    first.run_cycle()
    assert second.get_charges("alice") == []
    assert second.run_cycle() == 100
