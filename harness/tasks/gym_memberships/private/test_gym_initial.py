"""Hidden tests for the initial gym_memberships spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with gym.py importable, e.g. in the sandbox):
    python -m pytest private/test_gym_initial.py
"""

import pytest
from gym import Gym, GymError

BAD_DAYS = [0, -3, 2.5, "7", None]


@pytest.fixture
def gym():
    g = Gym()
    g.add_plan("basic")
    g.add_plan("premium")
    g.add_member("ann", "basic")
    g.add_member("ben", "premium")
    return g


def state(g):
    """Every member's plan and check-ins, to check that a failed call changed nothing."""
    return {m: (g.get_plan(m), g.get_check_ins(m)) for m in g.get_members()}


# --- plans ------------------------------------------------------------------


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_plan_ids_are_rejected(bad_id):
    g = Gym()
    with pytest.raises(ValueError):
        g.add_plan(bad_id)
    with pytest.raises(KeyError):
        g.add_member("ann", bad_id)


def test_adding_a_plan_twice_is_rejected(gym):
    with pytest.raises(GymError):
        gym.add_plan("basic")
    assert gym.get_members("basic") == ["ann"]


@pytest.mark.parametrize(
    "call",
    [
        lambda g: g.add_member("cat", "gold"),
        lambda g: g.change_plan("ann", "gold"),
        lambda g: g.get_members("gold"),
        lambda g: g.get_members(1),
    ],
)
def test_plans_that_do_not_exist_raise_key_error(gym, call):
    before = state(gym)
    with pytest.raises(KeyError):
        call(gym)
    assert state(gym) == before
    assert gym.get_members() == ["ann", "ben"]


# --- members ----------------------------------------------------------------


def test_a_new_member_starts_with_no_check_ins(gym):
    assert gym.get_plan("ben") == "premium"
    assert gym.get_check_ins("ben") == []


def test_members_are_listed_in_joining_order():
    g = Gym()
    g.add_plan("basic")
    for name in ["cat", "ann", "ben"]:
        g.add_member(name, "basic")
    assert g.get_members() == ["cat", "ann", "ben"]
    assert g.get_members("basic") == ["cat", "ann", "ben"]


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_member_ids_are_rejected(gym, bad_id):
    with pytest.raises(ValueError):
        gym.add_member(bad_id, "basic")
    assert gym.get_members() == ["ann", "ben"]


def test_adding_a_member_twice_is_rejected(gym):
    gym.check_in("ann", 2)
    before = state(gym)
    with pytest.raises(GymError):
        gym.add_member("ann", "premium")
    assert state(gym) == before
    assert gym.get_members() == ["ann", "ben"]


def test_a_bad_member_id_is_reported_before_an_unknown_plan(gym):
    with pytest.raises(ValueError):
        gym.add_member("", "gold")


def test_an_unknown_plan_is_reported_before_a_duplicate_member(gym):
    with pytest.raises(KeyError):
        gym.add_member("ann", "gold")
    assert gym.get_plan("ann") == "basic"


@pytest.mark.parametrize(
    "call",
    [
        lambda g: g.change_plan("cat", "basic"),
        lambda g: g.check_in("cat", 1),
        lambda g: g.get_plan("cat"),
        lambda g: g.get_check_ins("cat"),
        lambda g: g.get_plan(None),
        lambda g: g.check_in(1, 1),
    ],
)
def test_members_that_do_not_exist_raise_key_error(gym, call):
    gym.check_in("ann", 1)
    before = state(gym)
    with pytest.raises(KeyError):
        call(gym)
    assert state(gym) == before


def test_changing_plan_moves_the_member(gym):
    gym.change_plan("ann", "premium")
    assert gym.get_plan("ann") == "premium"
    assert gym.get_members("basic") == []
    assert gym.get_members("premium") == ["ann", "ben"]
    gym.change_plan("ann", "basic")
    assert gym.get_members("basic") == ["ann"]


def test_changing_to_the_current_plan_is_rejected(gym):
    before = state(gym)
    with pytest.raises(GymError):
        gym.change_plan("ann", "basic")
    assert state(gym) == before


def test_an_unknown_member_is_reported_before_an_unknown_plan(gym):
    with pytest.raises(KeyError):
        gym.change_plan("cat", "gold")


def test_check_ins_survive_a_plan_change(gym):
    gym.check_in("ann", 1)
    gym.check_in("ann", 2)
    gym.change_plan("ann", "premium")
    assert gym.get_check_ins("ann") == [1, 2]
    assert gym.get_plan("ann") == "premium"


# --- check-ins --------------------------------------------------------------


def test_check_ins_keep_the_order_they_were_recorded_in(gym):
    for day in [5, 2, 9, 3]:
        gym.check_in("ann", day)
    assert gym.get_check_ins("ann") == [5, 2, 9, 3]


def test_members_check_in_independently(gym):
    gym.check_in("ann", 1)
    gym.check_in("ben", 1)
    gym.check_in("ben", 2)
    assert gym.get_check_ins("ann") == [1]
    assert gym.get_check_ins("ben") == [1, 2]


def test_a_repeated_day_is_rejected_and_changes_nothing(gym):
    gym.check_in("ann", 7)
    gym.check_in("ann", 8)
    before = state(gym)
    with pytest.raises(GymError):
        gym.check_in("ann", 7)
    assert state(gym) == before


def test_the_same_day_is_fine_for_different_members(gym):
    gym.check_in("ann", 7)
    gym.check_in("ben", 7)
    assert gym.get_check_ins("ben") == [7]


@pytest.mark.parametrize("day", BAD_DAYS)
def test_invalid_days_are_rejected(gym, day):
    gym.check_in("ann", 1)
    before = state(gym)
    with pytest.raises(ValueError):
        gym.check_in("ann", day)
    assert state(gym) == before


def test_an_unknown_member_is_reported_before_a_bad_day(gym):
    with pytest.raises(KeyError):
        gym.check_in("cat", -1)


def test_failed_calls_record_no_check_ins(gym):
    gym.check_in("ann", 3)
    for call in (
        lambda: gym.check_in("ann", 3),
        lambda: gym.check_in("ann", 0),
        lambda: gym.check_in("cat", 3),
        lambda: gym.change_plan("ann", "basic"),
    ):
        with pytest.raises((GymError, ValueError, KeyError)):
            call()
    assert gym.get_check_ins("ann") == [3]
    assert gym.get_check_ins("ben") == []


def test_gyms_do_not_share_plans_or_members():
    first, second = Gym(), Gym()
    first.add_plan("basic")
    first.add_member("ann", "basic")
    assert second.get_members() == []
    with pytest.raises(KeyError):
        second.add_member("ben", "basic")
    second.add_plan("basic")
    second.add_member("ann", "basic")
    assert second.get_check_ins("ann") == []
