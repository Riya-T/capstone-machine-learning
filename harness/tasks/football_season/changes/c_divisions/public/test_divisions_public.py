"""Public checks for the c_divisions change (divisions). Shown to the editor,
never to the writer.

Usage (with season.py importable, e.g. in the sandbox):
    python -m pytest changes/c_divisions/public/test_divisions_public.py
"""

from season import Season


def make_season():
    s = Season()
    s.add_team("Bears", division="North")
    s.add_team("Lions", division="North")
    s.add_team("Cowboys", division="East")
    return s


def test_division_standings_list_only_that_division():
    s = make_season()
    s.record_game("Lions", "Bears", 20, 10)
    assert s.get_standings("North") == ["Lions", "Bears"]
    assert s.get_standings() == ["Lions", "Cowboys", "Bears"]


def test_teams_without_a_division_have_no_division_games():
    s = make_season()
    s.add_team("Jets")
    s.add_team("Giants")
    s.record_game("Jets", "Giants", 20, 3)
    record = s.get_record("Jets")
    assert record["wins"] == 1
    assert (record["division_wins"], record["division_losses"], record["division_ties"]) == (0, 0, 0)


def test_division_games_are_counted_separately():
    s = make_season()
    s.record_game("Lions", "Bears", 20, 10)
    s.record_game("Bears", "Cowboys", 14, 7)
    record = s.get_record("Bears")
    assert (record["wins"], record["losses"]) == (1, 1)
    assert (record["division_wins"], record["division_losses"]) == (0, 1)
