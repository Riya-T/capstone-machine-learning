"""Hidden tests for the c_visits change (visit counts). Never shown to the
writer or the editor.

Usage (with gym.py importable, e.g. in the sandbox):
    python -m pytest changes/c_visits/private/test_visits_new.py
"""

import pytest
from gym import Gym


@pytest.fixture
def gym():
    g = Gym()
    g.add_plan("basic")
    g.add_plan("premium")
    g.add_plan("student")
    g.add_member("ann", "basic")
    g.add_member("ben", "premium")
    g.add_member("cat", "basic")
    return g


def test_counts_start_at_zero(gym):
    assert gym.get_visit_count("ann") == 0
    assert gym.get_visit_count("ann", "basic") == 0
    assert gym.get_plan_visits("basic") == 0
    assert gym.get_leaderboard() == ["ann", "ben", "cat"]


def test_count_matches_the_recorded_check_ins(gym):
    for day in [4, 1, 9]:
        gym.check_in("ann", day)
    assert gym.get_visit_count("ann") == 3
    assert gym.get_visit_count("ben") == 0


def test_check_ins_stay_with_the_plan_they_were_made_on(gym):
    gym.check_in("ann", 1)
    gym.change_plan("ann", "premium")
    gym.check_in("ann", 2)
    gym.check_in("ann", 3)
    gym.change_plan("ann", "basic")
    gym.check_in("ann", 4)
    assert gym.get_visit_count("ann", "basic") == 2
    assert gym.get_visit_count("ann", "premium") == 2
    assert gym.get_visit_count("ann", "student") == 0
    assert gym.get_visit_count("ann") == 4


def test_plan_visits_add_up_over_members_and_moves(gym):
    gym.check_in("ann", 1)
    gym.check_in("cat", 1)
    gym.check_in("cat", 2)
    gym.change_plan("cat", "premium")
    gym.check_in("cat", 3)
    gym.check_in("ben", 3)
    assert gym.get_plan_visits("basic") == 3
    assert gym.get_plan_visits("premium") == 2
    assert gym.get_plan_visits("student") == 0


def test_a_plan_the_member_never_had_counts_zero(gym):
    gym.check_in("ann", 1)
    assert gym.get_visit_count("ann", "student") == 0
    assert gym.get_visit_count("ann", "premium") == 0


def test_count_rejects_unknown_members_and_plans(gym):
    with pytest.raises(KeyError):
        gym.get_visit_count("dan")
    with pytest.raises(KeyError):
        gym.get_visit_count("dan", "basic")
    with pytest.raises(KeyError):
        gym.get_visit_count("ann", "gold")
    with pytest.raises(KeyError):
        gym.get_visit_count(None)


def test_plan_visits_rejects_unknown_plans(gym):
    with pytest.raises(KeyError):
        gym.get_plan_visits("gold")
    with pytest.raises(KeyError):
        gym.get_plan_visits(None)


def test_leaderboard_orders_by_count_then_joining_order(gym):
    gym.check_in("cat", 1)
    gym.check_in("cat", 2)
    gym.check_in("ann", 1)
    gym.check_in("ben", 1)
    assert gym.get_leaderboard() == ["cat", "ann", "ben"]
    gym.check_in("ben", 2)
    gym.check_in("ben", 3)
    assert gym.get_leaderboard() == ["ben", "cat", "ann"]


def test_leaderboard_ignores_which_plan_visits_were_on(gym):
    gym.check_in("ben", 1)
    gym.change_plan("ben", "basic")
    gym.check_in("ben", 2)
    gym.check_in("ann", 5)
    assert gym.get_leaderboard() == ["ben", "ann", "cat"]


def test_failed_check_ins_do_not_count(gym):
    gym.check_in("ann", 1)
    for call in (
        lambda: gym.check_in("ann", 1),
        lambda: gym.check_in("ann", -1),
        lambda: gym.check_in("dan", 2),
    ):
        with pytest.raises(Exception):
            call()
    assert gym.get_visit_count("ann") == 1
    assert gym.get_plan_visits("basic") == 1
