"""Public checks for the c_proration change (adjustable upgrade charge).
Shown to the editor, never to the writer.

Usage (with billing.py importable, e.g. in the sandbox):
    python -m pytest changes/c_proration/public/test_proration_public.py
"""

from billing import BillingSystem


def test_the_system_charges_a_share_of_the_difference():
    billing = BillingSystem(upgrade_percent=50)
    billing.add_plan("basic", 900)
    billing.add_plan("pro", 1500)
    billing.subscribe("alice", "basic")
    assert billing.get_upgrade_charge("alice", "pro") == 300
    billing.change_plan("alice", "pro")
    assert billing.get_charges("alice") == [300]
    assert billing.get_upgrade_percent("pro") == 50


def test_a_plan_can_set_its_own_percentage():
    billing = BillingSystem()
    billing.add_plan("basic", 900)
    billing.add_plan("pro", 1500, upgrade_percent=0)
    billing.subscribe("alice", "basic")
    billing.change_plan("alice", "pro")
    assert billing.get_charges("alice") == []
    assert billing.get_upgrade_percent("basic") == 100
