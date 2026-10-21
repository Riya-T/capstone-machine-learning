"""Hidden tests for the c_tiers change (plan tiers). Never shown to the
writer or the editor.

Usage (with gym.py importable, e.g. in the sandbox):
    python -m pytest changes/c_tiers/private/test_tiers_new.py
"""

import pytest
from gym import Gym, GymError

BAD_TIERS = ["", 3, None, 2.5]


@pytest.fixture
def gym():
    g = Gym()
    g.add_plan("basic")
    g.add_plan("gold", tier="premium")
    g.add_plan("student")
    g.add_member("ann", "basic")
    g.add_member("ben", "gold")
    g.add_member("cat", "student")
    return g


def state(g):
    plans = {p: g.get_tier(p) for p in g.get_plans()}
    members = {m: (g.get_plan(m), g.get_check_ins(m)) for m in g.get_members()}
    return plans, members


def test_new_plans_default_to_the_standard_tier(gym):
    assert gym.get_tier("basic") == "standard"
    assert gym.get_tier("student") == "standard"
    assert gym.get_tier("gold") == "premium"


def test_get_plans_keeps_the_order_plans_were_added(gym):
    gym.add_plan("family", tier="premium")
    assert gym.get_plans() == ["basic", "gold", "student", "family"]
    assert gym.get_plans(tier="premium") == ["gold", "family"]
    assert gym.get_plans(tier="standard") == ["basic", "student"]
    assert gym.get_plans(tier="corporate") == []


def test_set_tier_moves_a_plan(gym):
    gym.set_tier("student", "discount")
    assert gym.get_tier("student") == "discount"
    assert gym.get_plans(tier="standard") == ["basic"]
    assert gym.get_plans(tier="discount") == ["student"]


def test_setting_the_tier_a_plan_already_has_changes_nothing(gym):
    before = state(gym)
    gym.set_tier("gold", "premium")
    assert state(gym) == before


def test_members_in_tier_are_in_joining_order(gym):
    gym.add_plan("silver", tier="premium")
    gym.add_member("dan", "basic")
    gym.change_plan("ann", "silver")
    assert gym.get_members_in_tier("premium") == ["ann", "ben"]
    assert gym.get_members_in_tier("standard") == ["cat", "dan"]
    assert gym.get_members_in_tier("corporate") == []


def test_members_in_tier_follow_set_tier(gym):
    gym.set_tier("basic", "premium")
    assert gym.get_members_in_tier("premium") == ["ann", "ben"]
    assert gym.get_members_in_tier("standard") == ["cat"]


@pytest.mark.parametrize("tier", BAD_TIERS)
def test_invalid_tiers_are_rejected_when_adding_a_plan(gym, tier):
    before = state(gym)
    with pytest.raises(ValueError):
        gym.add_plan("family", tier=tier)
    assert state(gym) == before
    assert gym.get_plans() == ["basic", "gold", "student"]


@pytest.mark.parametrize("tier", BAD_TIERS)
def test_invalid_tiers_are_rejected_when_setting(gym, tier):
    before = state(gym)
    with pytest.raises(ValueError):
        gym.set_tier("basic", tier)
    assert state(gym) == before


@pytest.mark.parametrize("tier", BAD_TIERS)
def test_invalid_tiers_are_rejected_in_queries(gym, tier):
    if tier is not None:  # get_plans(tier=None) means every plan
        with pytest.raises(ValueError):
            gym.get_plans(tier=tier)
    with pytest.raises(ValueError):
        gym.get_members_in_tier(tier)


def test_tier_methods_reject_unknown_plans(gym):
    with pytest.raises(KeyError):
        gym.get_tier("family")
    with pytest.raises(KeyError):
        gym.set_tier("family", "premium")
    with pytest.raises(KeyError):
        gym.get_tier(None)


def test_an_unknown_plan_is_reported_before_a_bad_tier(gym):
    with pytest.raises(KeyError):
        gym.set_tier("family", "")


def test_a_duplicate_plan_is_reported_after_a_bad_tier(gym):
    with pytest.raises(ValueError):
        gym.add_plan("basic", tier="")
    with pytest.raises(GymError):
        gym.add_plan("basic", tier="premium")
    assert gym.get_tier("basic") == "standard"


def test_tiers_do_not_change_plan_lookups(gym):
    gym.set_tier("basic", "premium")
    assert gym.get_plan("ann") == "basic"
    assert gym.get_members("basic") == ["ann"]
    gym.check_in("ann", 1)
    assert gym.get_check_ins("ann") == [1]
