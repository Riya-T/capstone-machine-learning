"""Hidden tests for the c_pause change (paused subscriptions). Never shown to
the writer or the editor.

Usage (with billing.py importable, e.g. in the sandbox):
    python -m pytest changes/c_pause/private/test_pause_new.py
"""

import pytest
from billing import BillingError, BillingSystem, SubscriptionPaused


@pytest.fixture
def billing():
    b = BillingSystem()
    b.add_plan("basic", 900)
    b.add_plan("pro", 1500)
    b.subscribe("alice", "basic")
    b.subscribe("bob", "pro")
    return b


def state(b):
    return {c: (b.get_plan(c), b.get_charges(c), b.is_paused(c)) for c in ["alice", "bob"]}


def test_pause_new_subscriptions_are_not_paused(billing):
    assert not billing.is_paused("alice")
    assert not billing.is_paused("bob")


def test_pause_keeps_the_plan_and_charges_nothing(billing):
    billing.pause("bob")
    assert billing.get_plan("bob") == "pro"
    assert billing.get_charges("bob") == []
    billing.resume("bob")
    assert billing.get_charges("bob") == []
    assert not billing.is_paused("bob")


def test_pause_skips_cycles_until_resumed(billing):
    billing.run_cycle()
    billing.pause("bob")
    assert billing.run_cycle() == 900
    assert billing.run_cycle() == 900
    billing.resume("bob")
    assert billing.run_cycle() == 2400
    assert billing.get_charges("bob") == [1500, 1500]
    assert billing.get_charges("alice") == [900, 900, 900, 900]


def test_pause_everyone_gives_an_empty_cycle(billing):
    billing.pause("alice")
    billing.pause("bob")
    assert billing.run_cycle() == 0


def test_pause_twice_raises_subscription_paused(billing):
    billing.pause("alice")
    before = state(billing)
    with pytest.raises(SubscriptionPaused):
        billing.pause("alice")
    assert state(billing) == before


def test_pause_resume_when_not_paused_raises(billing):
    before = state(billing)
    with pytest.raises(BillingError) as info:
        billing.resume("alice")
    assert not isinstance(info.value, SubscriptionPaused)
    assert state(billing) == before


def test_pause_blocks_plan_changes_and_quotes(billing):
    billing.pause("alice")
    before = state(billing)
    with pytest.raises(SubscriptionPaused):
        billing.change_plan("alice", "pro")
    with pytest.raises(SubscriptionPaused):
        billing.get_upgrade_charge("alice", "pro")
    assert state(billing) == before
    billing.resume("alice")
    billing.change_plan("alice", "pro")
    assert billing.get_charges("alice") == [600]


def test_pause_change_plan_error_order(billing):
    billing.pause("alice")
    with pytest.raises(KeyError):
        billing.change_plan("alice", "gold")
    # paused and already on the plan: paused comes first
    with pytest.raises(SubscriptionPaused):
        billing.change_plan("alice", "basic")


def test_pause_a_paused_customer_may_cancel(billing):
    billing.pause("alice")
    billing.cancel("alice")
    assert billing.get_plan("alice") is None
    assert not billing.is_paused("alice")
    assert billing.run_cycle() == 1500


def test_pause_cancelled_customers(billing):
    billing.cancel("alice")
    for method in ("pause", "resume"):
        with pytest.raises(BillingError) as info:
            getattr(billing, method)("alice")
        assert not isinstance(info.value, SubscriptionPaused)
    assert not billing.is_paused("alice")


def test_pause_resubscribing_starts_unpaused(billing):
    billing.pause("alice")
    billing.cancel("alice")
    billing.subscribe("alice", "pro")
    assert not billing.is_paused("alice")
    assert billing.run_cycle() == 3000


@pytest.mark.parametrize("method", ["pause", "resume", "is_paused"])
def test_pause_unknown_customers_raise_key_error(billing, method):
    with pytest.raises(KeyError):
        getattr(billing, method)("carol")
    with pytest.raises(KeyError):
        getattr(billing, method)(None)


def test_subscription_paused_is_a_billing_error():
    assert issubclass(SubscriptionPaused, BillingError)
