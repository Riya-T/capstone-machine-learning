"""Public checks for billing.py.

Usage (with billing.py importable, e.g. in the sandbox):
    python -m pytest public/test_billing_public.py
"""

import pytest
from billing import BillingError, BillingSystem


@pytest.fixture
def billing():
    b = BillingSystem()
    b.add_plan("basic", 900)
    b.add_plan("pro", 1500)
    return b


def test_a_cycle_charges_every_subscriber(billing):
    billing.subscribe("alice", "basic")
    billing.subscribe("bob", "pro")
    assert billing.run_cycle() == 2400
    assert billing.get_charges("alice") == [900]
    assert billing.get_charges("bob") == [1500]


def test_subscribing_charges_nothing(billing):
    billing.subscribe("alice", "basic")
    assert billing.get_plan("alice") == "basic"
    assert billing.get_charges("alice") == []


def test_moving_to_a_dearer_plan_charges_the_difference(billing):
    billing.subscribe("alice", "basic")
    billing.change_plan("alice", "pro")
    assert billing.get_plan("alice") == "pro"
    assert billing.get_charges("alice") == [600]
    billing.run_cycle()
    assert billing.get_charges("alice") == [600, 1500]


def test_a_cancelled_customer_has_no_plan(billing):
    billing.subscribe("alice", "basic")
    billing.cancel("alice")
    assert billing.get_plan("alice") is None
    with pytest.raises(BillingError):
        billing.cancel("alice")


def test_subscribing_twice_raises(billing):
    billing.subscribe("alice", "basic")
    with pytest.raises(BillingError):
        billing.subscribe("alice", "pro")
    assert billing.get_plan("alice") == "basic"


def test_unknown_names_raise_key_error(billing):
    with pytest.raises(KeyError):
        billing.get_charges("carol")
    with pytest.raises(KeyError):
        billing.subscribe("carol", "gold")
