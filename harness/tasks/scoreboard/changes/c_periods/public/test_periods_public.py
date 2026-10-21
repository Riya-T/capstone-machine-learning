"""Public checks for the c_periods change (scores per period). Shown to the
editor, never to the writer.

Usage (with scoreboard.py importable, e.g. in the sandbox):
    python -m pytest changes/c_periods/public/test_periods_public.py
"""

from scoreboard import Scoreboard


def test_periods_scores_are_split_by_period():
    sb = Scoreboard()
    sb.add_team("lions")
    assert sb.get_period() == 1
    sb.score("lions", "try")
    assert sb.next_period() == 2
    sb.score("lions", "conversion")
    assert sb.get_period_scores("lions") == [5, 2]
    assert sb.get_score("lions") == 7
    assert sb.get_events("lions", period=2) == [("conversion", 2)]


def test_periods_a_quiet_period_counts_as_zero():
    sb = Scoreboard()
    sb.add_team("lions")
    sb.next_period()
    sb.next_period()
    sb.score("lions", "drop_goal")
    assert sb.get_period_scores("lions") == [0, 0, 3]
