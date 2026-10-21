"""Public checks for the c_tiers change (plan tiers). Shown to the editor,
never to the writer.

Usage (with gym.py importable, e.g. in the sandbox):
    python -m pytest changes/c_tiers/public/test_tiers_public.py
"""

import pytest
from gym import Gym


def test_plans_are_grouped_by_tier():
    g = Gym()
    g.add_plan("basic")
    g.add_plan("gold", tier="premium")
    g.add_plan("student")
    assert g.get_tier("basic") == "standard"
    assert g.get_tier("gold") == "premium"
    assert g.get_plans() == ["basic", "gold", "student"]
    assert g.get_plans(tier="standard") == ["basic", "student"]
    assert g.get_plans(tier="premium") == ["gold"]
    assert g.get_plans(tier="family") == []


def test_members_in_a_tier_follow_their_current_plan():
    g = Gym()
    g.add_plan("basic")
    g.add_plan("gold", tier="premium")
    g.add_member("ann", "basic")
    g.add_member("ben", "gold")
    assert g.get_members_in_tier("standard") == ["ann"]
    g.set_tier("basic", "premium")
    assert g.get_members_in_tier("premium") == ["ann", "ben"]
    assert g.get_members_in_tier("standard") == []


def test_tiers_must_be_non_empty_strings():
    g = Gym()
    with pytest.raises(ValueError):
        g.add_plan("basic", tier="")
    with pytest.raises(ValueError):
        g.get_plans(tier=3)
