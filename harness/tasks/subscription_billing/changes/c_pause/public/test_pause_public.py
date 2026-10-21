"""Public checks for the c_pause change (paused subscriptions). Shown to the
editor, never to the writer.

Usage (with billing.py importable, e.g. in the sandbox):
    python -m pytest changes/c_pause/public/test_pause_public.py
"""

import pytest
from billing import BillingSystem, SubscriptionPaused


def test_a_paused_customer_is_not_charged():
    billing = BillingSystem()
    billing.add_plan("basic", 900)
    billing.subscribe("alice", "basic")
    billing.subscribe("bob", "basic")
    billing.pause("alice")
    assert billing.is_paused("alice")
    assert billing.run_cycle() == 900
    billing.resume("alice")
    assert billing.run_cycle() == 1800
    assert billing.get_charges("alice") == [900]


def test_a_paused_customer_cannot_change_plan():
    billing = BillingSystem()
    billing.add_plan("basic", 900)
    billing.add_plan("pro", 1500)
    billing.subscribe("alice", "basic")
    billing.pause("alice")
    with pytest.raises(SubscriptionPaused):
        billing.change_plan("alice", "pro")
    assert billing.get_plan("alice") == "basic"
