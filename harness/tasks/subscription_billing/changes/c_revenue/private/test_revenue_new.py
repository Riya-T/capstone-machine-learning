"""Hidden tests for the c_revenue change (revenue reports). Never shown to
the writer or the editor.

Usage (with billing.py importable, e.g. in the sandbox):
    python -m pytest changes/c_revenue/private/test_revenue_new.py
"""

import pytest
from billing import BillingError, BillingSystem


@pytest.fixture
def billing():
    b = BillingSystem()
    b.add_plan("lite", 400)
    b.add_plan("basic", 900)
    b.add_plan("pro", 1500)
    b.subscribe("alice", "basic")
    b.subscribe("bob", "pro")
    return b


def test_revenue_starts_at_zero(billing):
    assert [billing.get_revenue(p) for p in ["lite", "basic", "pro"]] == [0, 0, 0]
    assert billing.get_total_revenue() == 0
    assert billing.get_plans_by_revenue() == ["lite", "basic", "pro"]


def test_revenue_follows_the_plan_in_each_cycle(billing):
    billing.run_cycle()
    billing.change_plan("alice", "lite")
    billing.run_cycle()
    assert billing.get_revenue("basic") == 900
    assert billing.get_revenue("lite") == 400
    assert billing.get_revenue("pro") == 3000
    assert billing.get_total_revenue() == 4300


def test_revenue_keeps_charges_after_cancelling(billing):
    billing.run_cycle()
    billing.cancel("bob")
    billing.run_cycle()
    assert billing.get_revenue("pro") == 1500
    assert billing.get_total_revenue() == 3300


def test_revenue_upgrade_charges_count_for_the_target_plan(billing):
    billing.change_plan("alice", "lite")
    billing.change_plan("alice", "pro")
    assert billing.get_revenue("pro") == 1100
    assert billing.get_revenue("lite") == 0
    assert billing.get_revenue("basic") == 0
    assert billing.get_total_revenue() == 1100


def test_revenue_total_matches_every_charge(billing):
    billing.run_cycle()
    billing.change_plan("alice", "pro")
    billing.cancel("bob")
    billing.subscribe("carol", "lite")
    billing.run_cycle()
    total = sum(sum(billing.get_charges(c)) for c in ["alice", "bob", "carol"])
    assert billing.get_total_revenue() == total == 900 + 1500 + 600 + 1500 + 400


def test_revenue_ranking_highest_first(billing):
    billing.run_cycle()
    # pro 1500, basic 900, lite 0
    assert billing.get_plans_by_revenue() == ["pro", "basic", "lite"]
    billing.subscribe("carol", "lite")
    billing.change_plan("bob", "lite")
    for _ in range(4):
        billing.run_cycle()
    # lite 3200, basic 4500, pro 1500
    assert billing.get_plans_by_revenue() == ["basic", "lite", "pro"]


def test_revenue_ties_keep_the_order_added():
    b = BillingSystem()
    for plan_id in ["gold", "silver", "bronze"]:
        b.add_plan(plan_id, 500)
    b.subscribe("alice", "bronze")
    b.subscribe("bob", "gold")
    b.run_cycle()
    assert b.get_plans_by_revenue() == ["gold", "bronze", "silver"]


def test_revenue_failed_calls_add_nothing(billing):
    billing.run_cycle()
    for call in (
        lambda: billing.change_plan("alice", "basic"),
        lambda: billing.change_plan("alice", "gold"),
        lambda: billing.subscribe("alice", "pro"),
    ):
        with pytest.raises((KeyError, BillingError)):
            call()
    assert billing.get_total_revenue() == 2400


def test_revenue_unknown_plan_raises_key_error(billing):
    with pytest.raises(KeyError):
        billing.get_revenue("gold")
    with pytest.raises(KeyError):
        billing.get_revenue(None)


def test_revenue_includes_new_plans(billing):
    billing.add_plan("max", 2500)
    billing.change_plan("bob", "max")
    assert billing.get_plans_by_revenue() == ["max", "lite", "basic", "pro"]
    assert billing.get_revenue("max") == 1000
