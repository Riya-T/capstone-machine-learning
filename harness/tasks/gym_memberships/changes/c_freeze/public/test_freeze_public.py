"""Public checks for the c_freeze change (frozen memberships). Shown to the
editor, never to the writer.

Usage (with gym.py importable, e.g. in the sandbox):
    python -m pytest changes/c_freeze/public/test_freeze_public.py
"""

import pytest
from gym import Gym, MembershipFrozen


def test_a_frozen_member_cannot_check_in():
    g = Gym()
    g.add_plan("basic")
    g.add_member("ann", "basic")
    g.freeze("ann")
    assert g.is_frozen("ann")
    with pytest.raises(MembershipFrozen):
        g.check_in("ann", 1)
    g.unfreeze("ann")
    g.check_in("ann", 1)
    assert g.get_check_ins("ann") == [1]


def test_active_only_leaves_frozen_members_out():
    g = Gym()
    g.add_plan("basic")
    g.add_member("ann", "basic")
    g.add_member("ben", "basic")
    g.freeze("ann")
    assert g.get_members() == ["ann", "ben"]
    assert g.get_members(active_only=True) == ["ben"]
