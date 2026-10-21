"""Hidden tests for the c_proration change (adjustable upgrade charge).
Never shown to the writer or the editor.

Usage (with billing.py importable, e.g. in the sandbox):
    python -m pytest changes/c_proration/private/test_proration_new.py
"""

import pytest
from billing import BillingError, BillingSystem

BAD_PERCENTS = [-1, 101, 50.0, "50", True]


def make(percent=100, **plan_percents):
    b = BillingSystem(upgrade_percent=percent)
    for plan_id, price in [("lite", 400), ("basic", 900), ("plus", 1000), ("pro", 1500)]:
        b.add_plan(plan_id, price, upgrade_percent=plan_percents.get(plan_id))
    b.subscribe("alice", "basic")
    return b


def test_proration_default_charges_the_whole_difference():
    b = make()
    assert b.get_upgrade_percent("pro") == 100
    b.change_plan("alice", "pro")
    assert b.get_charges("alice") == [600]


def test_proration_rounds_down():
    b = make(percent=33)
    assert b.get_upgrade_charge("alice", "plus") == 33
    b.change_plan("alice", "plus")
    b.change_plan("alice", "pro")
    # 100 * 33 // 100 = 33, then 500 * 33 // 100 = 165
    assert b.get_charges("alice") == [33, 165]


def test_proration_uses_the_percentage_of_the_target_plan():
    b = make(percent=50, pro=10, lite=0)
    b.change_plan("alice", "pro")
    assert b.get_charges("alice") == [60]
    b.change_plan("alice", "lite")
    b.change_plan("alice", "plus")
    assert b.get_charges("alice") == [60, 300]
    assert [b.get_upgrade_percent(p) for p in ["lite", "basic", "plus", "pro"]] == [0, 50, 50, 10]


def test_proration_zero_charge_adds_no_entry():
    b = make(percent=0)
    assert b.get_upgrade_charge("alice", "pro") == 0
    b.change_plan("alice", "pro")
    assert b.get_charges("alice") == []
    assert b.get_plan("alice") == "pro"


def test_proration_charge_that_rounds_to_zero_adds_no_entry():
    b = make(percent=1)
    # 100 * 1 // 100 = 1 is charged
    b.change_plan("alice", "plus")
    assert b.get_charges("alice") == [1]
    c = make(percent=50)
    c.add_plan("basic_plus", 901)
    # 1 * 50 // 100 = 0 is not
    assert c.get_upgrade_charge("alice", "basic_plus") == 0
    c.change_plan("alice", "basic_plus")
    assert c.get_charges("alice") == []
    assert c.get_plan("alice") == "basic_plus"


def test_proration_downgrades_stay_free():
    b = make(percent=100, lite=100)
    assert b.get_upgrade_charge("alice", "lite") == 0
    b.change_plan("alice", "lite")
    assert b.get_charges("alice") == []


def test_proration_cycles_still_charge_full_price():
    b = make(percent=20)
    b.change_plan("alice", "pro")
    assert b.run_cycle() == 1500
    assert b.get_charges("alice") == [120, 1500]


def test_proration_quote_changes_nothing():
    b = make(percent=50)
    for _ in range(2):
        assert b.get_upgrade_charge("alice", "pro") == 300
    assert b.get_plan("alice") == "basic"
    assert b.get_charges("alice") == []


def test_proration_quote_raises_like_change_plan():
    b = make()
    with pytest.raises(KeyError):
        b.get_upgrade_charge("carol", "pro")
    with pytest.raises(KeyError):
        b.get_upgrade_charge("alice", "gold")
    with pytest.raises(BillingError):
        b.get_upgrade_charge("alice", "basic")
    b.cancel("alice")
    with pytest.raises(KeyError):
        b.get_upgrade_charge("alice", "gold")
    with pytest.raises(BillingError):
        b.get_upgrade_charge("alice", "pro")


@pytest.mark.parametrize("bad", BAD_PERCENTS)
def test_proration_invalid_system_percent_is_rejected(bad):
    with pytest.raises(ValueError):
        BillingSystem(upgrade_percent=bad)


@pytest.mark.parametrize("bad", BAD_PERCENTS)
def test_proration_invalid_plan_percent_is_rejected(bad):
    b = BillingSystem()
    with pytest.raises(ValueError):
        b.add_plan("pro", 1500, upgrade_percent=bad)
    with pytest.raises(KeyError):
        b.get_upgrade_percent("pro")


def test_proration_add_plan_error_order():
    b = BillingSystem()
    b.add_plan("pro", 1500, upgrade_percent=40)
    with pytest.raises(ValueError):
        b.add_plan("", 1500, upgrade_percent=200)
    with pytest.raises(ValueError):
        b.add_plan("gold", 0, upgrade_percent=200)
    with pytest.raises(ValueError):
        b.add_plan("pro", 1500, upgrade_percent=200)
    with pytest.raises(BillingError):
        b.add_plan("pro", 900, upgrade_percent=10)
    assert b.get_upgrade_percent("pro") == 40


def test_proration_bounds_are_allowed():
    b = make(percent=0, pro=100)
    b.change_plan("alice", "plus")
    b.change_plan("alice", "pro")
    assert b.get_charges("alice") == [500]
    with pytest.raises(KeyError):
        b.get_upgrade_percent("gold")
