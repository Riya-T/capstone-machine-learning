"""Public checks for the c_seasons change (seasons). Shown to the editor,
never to the writer.

Usage (with scores.py importable, e.g. in the sandbox):
    python -m pytest changes/c_seasons/public/test_seasons_public.py
"""

from scores import ScoreBoard


def test_scores_fall_into_the_season_that_is_current():
    bd = ScoreBoard()
    bd.add_player("ana")
    bd.record_score("ana", 100)
    bd.start_season("spring")
    bd.record_score("ana", 250)
    assert bd.get_seasons() == ["default", "spring"]
    assert bd.get_current_season() == "spring"
    assert bd.get_scores("ana", season="default") == [100]
    assert bd.get_scores("ana", season="spring") == [250]
    assert bd.get_scores("ana") == [100, 250]


def test_totals_and_top_scores_can_be_limited_to_a_season():
    bd = ScoreBoard()
    bd.add_player("ana")
    bd.add_player("ben")
    bd.record_score("ana", 100)
    bd.record_score("ben", 400)
    bd.start_season("spring")
    bd.record_score("ana", 250)
    assert bd.get_total_score("ana", season="spring") == 250
    assert bd.get_total_score("ana") == 350
    assert bd.get_top_scores(5, season="spring") == [250]
    assert bd.get_top_scores(5) == [400, 250, 100]
