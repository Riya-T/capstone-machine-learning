"""Hidden tests for the c_freeze change (frozen memberships). Never shown to
the writer or the editor.

Usage (with gym.py importable, e.g. in the sandbox):
    python -m pytest changes/c_freeze/private/test_freeze_new.py
"""

import pytest
from gym import Gym, GymError, MembershipFrozen


@pytest.fixture
def gym():
    g = Gym()
    g.add_plan("basic")
    g.add_plan("premium")
    g.add_member("ann", "basic")
    g.add_member("ben", "premium")
    g.check_in("ann", 1)
    return g


def state(g):
    return {m: (g.get_plan(m), g.get_check_ins(m), g.is_frozen(m)) for m in g.get_members()}


def test_members_start_unfrozen(gym):
    assert not gym.is_frozen("ann")
    assert not gym.is_frozen("ben")


def test_freezing_or_unfreezing_twice_is_harmless(gym):
    gym.freeze("ann")
    gym.freeze("ann")
    assert gym.is_frozen("ann")
    assert not gym.is_frozen("ben")
    gym.unfreeze("ann")
    gym.unfreeze("ann")
    assert not gym.is_frozen("ann")


@pytest.mark.parametrize("method", ["freeze", "unfreeze", "is_frozen"])
def test_freeze_methods_reject_unknown_members(gym, method):
    with pytest.raises(KeyError):
        getattr(gym, method)("cat")
    with pytest.raises(KeyError):
        getattr(gym, method)(None)


def test_a_check_in_while_frozen_changes_nothing(gym):
    gym.freeze("ann")
    before = state(gym)
    with pytest.raises(MembershipFrozen):
        gym.check_in("ann", 2)
    assert state(gym) == before


def test_a_plan_change_while_frozen_changes_nothing(gym):
    gym.freeze("ann")
    before = state(gym)
    with pytest.raises(MembershipFrozen):
        gym.change_plan("ann", "premium")
    assert state(gym) == before
    assert gym.get_members("basic") == ["ann"]


def test_frozen_is_reported_before_a_repeated_day_or_same_plan(gym):
    gym.freeze("ann")
    with pytest.raises(MembershipFrozen):
        gym.check_in("ann", 1)
    with pytest.raises(MembershipFrozen):
        gym.change_plan("ann", "basic")


def test_bad_input_is_reported_before_frozen(gym):
    gym.freeze("ann")
    with pytest.raises(ValueError):
        gym.check_in("ann", 0)
    with pytest.raises(KeyError):
        gym.change_plan("ann", "gold")
    with pytest.raises(KeyError):
        gym.check_in("cat", 1)


def test_other_members_are_not_affected_by_a_freeze(gym):
    gym.freeze("ann")
    gym.check_in("ben", 1)
    gym.change_plan("ben", "basic")
    assert gym.get_check_ins("ben") == [1]
    assert gym.get_plan("ben") == "basic"


def test_active_only_filters_with_and_without_a_plan(gym):
    gym.add_member("cat", "basic")
    gym.freeze("ben")
    gym.freeze("cat")
    assert gym.get_members(active_only=True) == ["ann"]
    assert gym.get_members("basic", active_only=True) == ["ann"]
    assert gym.get_members("premium", active_only=True) == []
    assert gym.get_members("basic") == ["ann", "cat"]
    assert gym.get_members(active_only=False) == ["ann", "ben", "cat"]


def test_active_only_still_rejects_an_unknown_plan(gym):
    with pytest.raises(KeyError):
        gym.get_members("gold", active_only=True)


def test_membership_frozen_is_a_gym_error():
    assert issubclass(MembershipFrozen, GymError)


def test_freezing_keeps_plan_and_check_ins(gym):
    gym.freeze("ann")
    assert gym.get_plan("ann") == "basic"
    assert gym.get_check_ins("ann") == [1]
    gym.unfreeze("ann")
    gym.check_in("ann", 2)
    gym.change_plan("ann", "premium")
    assert gym.get_check_ins("ann") == [1, 2]
    assert gym.get_plan("ann") == "premium"
