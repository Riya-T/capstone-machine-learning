"""Public checks for the c_points change (adjustable point values). Shown to
the editor, never to the writer.

Usage (with scoreboard.py importable, e.g. in the sandbox):
    python -m pytest changes/c_points/public/test_points_public.py
"""

import pytest
from scoreboard import Scoreboard


def test_points_a_custom_table_replaces_the_standard_one():
    sb = Scoreboard(points={"goal": 1, "behind": 6})
    sb.add_team("lions")
    sb.score("lions", "behind")
    sb.score("lions", "goal")
    assert sb.get_score("lions") == 7
    assert sb.get_kinds() == ["goal", "behind"]
    with pytest.raises(ValueError):
        sb.score("lions", "try")


def test_points_new_values_apply_only_to_later_events():
    sb = Scoreboard()
    sb.add_team("lions")
    sb.score("lions", "try")
    sb.set_points("try", 4)
    sb.score("lions", "try")
    assert sb.get_points("try") == 4
    assert sb.get_events("lions") == [("try", 5), ("try", 4)]
    assert sb.get_score("lions") == 9
