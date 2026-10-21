"""Public checks for the c_visits change (visit counts). Shown to the editor,
never to the writer.

Usage (with gym.py importable, e.g. in the sandbox):
    python -m pytest changes/c_visits/public/test_visits_public.py
"""

from gym import Gym


def test_visit_counts_follow_the_plan_at_check_in_time():
    g = Gym()
    g.add_plan("basic")
    g.add_plan("premium")
    g.add_member("ann", "basic")
    g.check_in("ann", 1)
    g.check_in("ann", 2)
    g.change_plan("ann", "premium")
    g.check_in("ann", 3)
    assert g.get_visit_count("ann") == 3
    assert g.get_visit_count("ann", "basic") == 2
    assert g.get_visit_count("ann", "premium") == 1
    assert g.get_plan_visits("basic") == 2


def test_leaderboard_puts_the_most_visits_first():
    g = Gym()
    g.add_plan("basic")
    for name in ["ann", "ben", "cat"]:
        g.add_member(name, "basic")
    g.check_in("ben", 1)
    g.check_in("ben", 2)
    g.check_in("cat", 1)
    assert g.get_leaderboard() == ["ben", "cat", "ann"]
