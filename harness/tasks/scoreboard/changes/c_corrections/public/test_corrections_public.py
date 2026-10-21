"""Public checks for the c_corrections change (taking back events). Shown to
the editor, never to the writer.

Usage (with scoreboard.py importable, e.g. in the sandbox):
    python -m pytest changes/c_corrections/public/test_corrections_public.py
"""

import pytest
from scoreboard import Scoreboard, ScoreboardError


def test_corrections_undo_takes_back_the_latest_event():
    sb = Scoreboard()
    sb.add_team("lions")
    sb.score("lions", "try")
    sb.score("lions", "conversion")
    assert sb.undo_last("lions") == ("conversion", 2)
    assert sb.get_score("lions") == 5
    assert sb.get_events("lions") == [("try", 5)]
    assert sb.get_undone("lions") == [("conversion", 2)]


def test_corrections_nothing_left_to_undo_raises():
    sb = Scoreboard()
    sb.add_team("lions")
    with pytest.raises(ScoreboardError):
        sb.undo_last("lions")
    assert sb.get_undone("lions") == []
