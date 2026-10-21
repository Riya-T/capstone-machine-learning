"""Public checks for the c_revenue change (revenue reports). Shown to the
editor, never to the writer.

Usage (with billing.py importable, e.g. in the sandbox):
    python -m pytest changes/c_revenue/public/test_revenue_public.py
"""

from billing import BillingSystem


def test_revenue_counts_cycle_charges_per_plan():
    billing = BillingSystem()
    billing.add_plan("basic", 900)
    billing.add_plan("pro", 1500)
    billing.subscribe("alice", "basic")
    billing.run_cycle()
    billing.run_cycle()
    assert billing.get_revenue("basic") == 1800
    assert billing.get_revenue("pro") == 0
    assert billing.get_total_revenue() == 1800
    assert billing.get_plans_by_revenue() == ["basic", "pro"]


def test_an_upgrade_counts_for_the_new_plan():
    billing = BillingSystem()
    billing.add_plan("basic", 900)
    billing.add_plan("pro", 1500)
    billing.subscribe("alice", "basic")
    billing.change_plan("alice", "pro")
    assert billing.get_revenue("pro") == 600
    assert billing.get_revenue("basic") == 0
