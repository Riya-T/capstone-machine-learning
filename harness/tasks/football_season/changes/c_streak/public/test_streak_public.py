"""Public checks for the c_streak change (current streaks). Shown to the
editor, never to the writer.

Usage (with season.py importable, e.g. in the sandbox):
    python -m pytest changes/c_streak/public/test_streak_public.py
"""

from season import Season


def test_two_wins_in_a_row():
    s = Season()
    s.add_team("Bears")
    s.add_team("Lions")
    s.record_game("Bears", "Lions", 24, 17)
    s.record_game("Lions", "Bears", 3, 10)
    assert s.get_record("Bears")["streak"] == "W2"
    assert s.get_record("Lions")["streak"] == "L2"


def test_no_games_means_no_streak():
    s = Season()
    s.add_team("Bears")
    assert s.get_record("Bears")["streak"] == ""
