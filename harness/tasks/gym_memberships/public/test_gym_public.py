"""Public checks for gym.py.

Usage (with gym.py importable, e.g. in the sandbox):
    python -m pytest public/test_gym_public.py
"""

import pytest
from gym import Gym, GymError


@pytest.fixture
def gym():
    g = Gym()
    g.add_plan("basic")
    g.add_plan("premium")
    g.add_member("ann", "basic")
    g.add_member("ben", "premium")
    return g


def test_a_new_member_is_on_the_given_plan(gym):
    assert gym.get_plan("ann") == "basic"
    assert gym.get_check_ins("ann") == []


def test_check_ins_are_listed_in_the_order_recorded(gym):
    gym.check_in("ann", 3)
    gym.check_in("ann", 1)
    assert gym.get_check_ins("ann") == [3, 1]


def test_checking_in_twice_on_one_day_raises(gym):
    gym.check_in("ann", 4)
    with pytest.raises(GymError):
        gym.check_in("ann", 4)
    assert gym.get_check_ins("ann") == [4]


def test_members_can_be_listed_by_plan(gym):
    gym.change_plan("ben", "basic")
    assert gym.get_members() == ["ann", "ben"]
    assert gym.get_members("basic") == ["ann", "ben"]
    assert gym.get_members("premium") == []


def test_days_must_be_positive(gym):
    with pytest.raises(ValueError):
        gym.check_in("ann", 0)
    with pytest.raises(ValueError):
        gym.check_in("ann", -2)


def test_unknown_member_raises_key_error(gym):
    with pytest.raises(KeyError):
        gym.get_plan("cat")
