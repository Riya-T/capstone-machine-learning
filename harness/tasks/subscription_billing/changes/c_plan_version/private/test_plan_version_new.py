"""Hidden tests for the c_plan_version change (versioned subscriptions).
Never shown to the writer or the editor.

Usage (with billing.py importable, e.g. in the sandbox):
    python -m pytest changes/c_plan_version/private/test_plan_version_new.py
"""

import pytest
from billing import BillingError, BillingSystem, SubscriptionPaused, VersionConflict


@pytest.fixture
def billing():
    b = BillingSystem()
    b.add_plan("basic", 900)
    b.add_plan("pro", 1500)
    b.add_plan("lite", 400)
    b.subscribe("alice", "basic")
    b.subscribe("bob", "pro")
    return b


def state(b):
    return {
        c: (b.get_plan(c), b.get_charges(c), b.is_paused(c), b.get_version(c))
        for c in ["alice", "bob"]
    }


def test_versioned_subscriptions_start_at_one(billing):
    assert billing.get_version("alice") == 1
    assert billing.get_version("bob") == 1


def test_versioned_changes_each_add_one(billing):
    billing.change_plan("alice", "pro")
    billing.pause("alice")
    billing.resume("alice", expected_version=3)
    billing.change_plan("alice", "lite", expected_version=4)
    assert billing.get_version("alice") == 5
    assert billing.get_version("bob") == 1


def test_versioned_cycles_and_reads_leave_it_alone(billing):
    billing.run_cycle()
    billing.run_cycle()
    billing.get_plan("alice")
    billing.get_charges("alice")
    billing.get_upgrade_charge("alice", "pro")
    billing.is_paused("alice")
    assert billing.get_version("alice") == 1


def test_versioned_failed_calls_leave_it_alone(billing):
    billing.pause("alice")
    for call in (
        lambda: billing.pause("alice"),
        lambda: billing.change_plan("alice", "pro"),
        lambda: billing.change_plan("alice", "gold"),
        lambda: billing.resume("alice", expected_version=1),
    ):
        with pytest.raises((KeyError, BillingError)):
            call()
    assert billing.get_version("alice") == 2


@pytest.mark.parametrize(
    "call",
    [
        lambda b: b.change_plan("alice", "pro", expected_version=2),
        lambda b: b.pause("alice", expected_version=0),
        lambda b: b.resume("bob", expected_version=1),  # bob is paused, at version 2
        lambda b: b.cancel("alice", expected_version=2),
    ],
    ids=["change_plan", "pause", "resume", "cancel"],
)
def test_versioned_stale_calls_change_nothing(billing, call):
    billing.pause("bob")
    before = state(billing)
    with pytest.raises(VersionConflict):
        call(billing)
    assert state(billing) == before


def test_versioned_cancel_with_the_right_version(billing):
    billing.change_plan("bob", "basic")
    billing.cancel("bob", expected_version=2)
    assert billing.run_cycle() == 900


def test_versioned_matching_version_still_applies_the_rules(billing):
    billing.pause("alice")
    with pytest.raises(SubscriptionPaused):
        billing.change_plan("alice", "pro", expected_version=2)
    with pytest.raises(SubscriptionPaused):
        billing.pause("alice", expected_version=2)
    assert billing.get_version("alice") == 2


def test_versioned_unknown_customer_raises_key_error(billing):
    with pytest.raises(KeyError):
        billing.get_version("carol")
    with pytest.raises(KeyError):
        billing.get_version(None)


def test_version_conflict_is_a_billing_error():
    assert issubclass(VersionConflict, BillingError)
    assert not issubclass(VersionConflict, SubscriptionPaused)
