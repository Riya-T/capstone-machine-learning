"""Hidden tests for the c_points change (adjustable point values). Never
shown to the writer or the editor.

Usage (with scoreboard.py importable, e.g. in the sandbox):
    python -m pytest changes/c_points/private/test_points_new.py
"""

import pytest
from scoreboard import Scoreboard

BAD_TABLES = [{}, [], "try", {"": 1}, {5: 1}, {"goal": 0}, {"goal": -2}, {"goal": True},
              {"goal": 1.5}, {"goal": "3"}, {"goal": 2, "behind": None}]
BAD_VALUES = [0, -1, True, 2.5, "3", None]


def state(sb):
    teams = {t: (sb.get_score(t), sb.get_events(t)) for t in sb.get_teams()}
    return teams, sb.get_standings(), {k: sb.get_points(k) for k in sb.get_kinds()}


def test_points_the_default_table_is_the_standard_one():
    sb = Scoreboard()
    assert sb.get_kinds() == ["try", "conversion", "drop_goal"]
    assert [sb.get_points(k) for k in sb.get_kinds()] == [5, 2, 3]
    assert Scoreboard(points=None).get_kinds() == ["try", "conversion", "drop_goal"]


def test_points_only_kinds_of_a_custom_table_can_be_scored():
    sb = Scoreboard(points={"run": 1, "try": 4})
    sb.add_team("lions")
    sb.score("lions", "try")
    sb.score("lions", "run")
    assert sb.get_events("lions") == [("try", 4), ("run", 1)]
    before = state(sb)
    for kind in ["conversion", "drop_goal", "Run"]:
        with pytest.raises(ValueError):
            sb.score("lions", kind)
    assert state(sb) == before


def test_points_standings_use_the_custom_values():
    sb = Scoreboard(points={"small": 1, "big": 10})
    for name in ["lions", "hawks", "owls"]:
        sb.add_team(name)
    for _ in range(9):
        sb.score("lions", "small")
    sb.score("hawks", "big")
    sb.score("owls", "small")
    assert sb.get_standings() == ["hawks", "lions", "owls"]
    assert sb.get_score("lions") == 9


@pytest.mark.parametrize("table", BAD_TABLES)
def test_points_invalid_tables_are_rejected(table):
    with pytest.raises(ValueError):
        Scoreboard(points=table)


def test_points_the_table_passed_in_is_copied():
    table = {"goal": 3}
    sb = Scoreboard(points=table)
    table["goal"] = 100
    table["extra"] = 1
    sb.set_points("bonus", 2)
    assert table == {"goal": 100, "extra": 1}
    assert sb.get_kinds() == ["goal", "bonus"]
    assert sb.get_points("goal") == 3
    with pytest.raises(ValueError):
        sb.get_points("extra")


@pytest.mark.parametrize("kind", ["penalty", "", None, "Try"])
def test_points_get_points_rejects_unknown_kinds(kind):
    with pytest.raises(ValueError):
        Scoreboard().get_points(kind)


def test_points_set_points_does_not_rewrite_past_events():
    sb = Scoreboard()
    sb.add_team("lions")
    sb.add_team("hawks")
    sb.score("lions", "conversion")
    sb.score("hawks", "conversion")
    sb.set_points("conversion", 7)
    sb.score("hawks", "conversion")
    assert sb.get_events("lions") == [("conversion", 2)]
    assert sb.get_events("hawks") == [("conversion", 2), ("conversion", 7)]
    assert (sb.get_score("lions"), sb.get_score("hawks")) == (2, 9)
    sb.set_points("conversion", 1)
    assert (sb.get_score("lions"), sb.get_score("hawks")) == (2, 9)


def test_points_set_points_can_add_a_kind():
    sb = Scoreboard()
    sb.add_team("lions")
    sb.set_points("penalty_try", 7)
    sb.set_points("try", 6)  # an existing kind keeps its place
    assert sb.get_kinds() == ["try", "conversion", "drop_goal", "penalty_try"]
    sb.score("lions", "penalty_try")
    assert sb.get_events("lions") == [("penalty_try", 7)]


@pytest.mark.parametrize("value", BAD_VALUES)
def test_points_set_points_rejects_bad_values(value):
    sb = Scoreboard()
    sb.add_team("lions")
    sb.score("lions", "try")
    before = state(sb)
    with pytest.raises(ValueError):
        sb.set_points("try", value)
    with pytest.raises(ValueError):
        sb.set_points("new_kind", value)
    assert state(sb) == before


@pytest.mark.parametrize("kind", ["", None, 3])
def test_points_set_points_rejects_bad_kinds(kind):
    sb = Scoreboard()
    with pytest.raises(ValueError):
        sb.set_points(kind, 4)
    assert sb.get_kinds() == ["try", "conversion", "drop_goal"]


def test_points_each_scoreboard_has_its_own_table():
    first = Scoreboard()
    first.set_points("try", 8)
    first.set_points("bonus", 1)
    second = Scoreboard()
    assert second.get_points("try") == 5
    assert second.get_kinds() == ["try", "conversion", "drop_goal"]
    second.add_team("lions")
    second.score("lions", "try")
    assert second.get_score("lions") == 5
