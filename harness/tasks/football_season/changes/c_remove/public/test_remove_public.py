"""Public checks for the c_remove change (removing games). Shown to the
editor, never to the writer.

Usage (with season.py importable, e.g. in the sandbox):
    python -m pytest changes/c_remove/public/test_remove_public.py
"""

import pytest
from season import Season


def test_removing_a_game_takes_back_the_result():
    s = Season()
    s.add_team("Bears")
    s.add_team("Lions")
    game_id = s.record_game("Bears", "Lions", 24, 17)
    s.remove_game(game_id)
    assert s.get_record("Bears")["wins"] == 0
    assert s.get_record("Lions")["points_against"] == 0


def test_a_removed_game_cannot_be_removed_again():
    s = Season()
    s.add_team("Bears")
    s.add_team("Lions")
    game_id = s.record_game("Bears", "Lions", 24, 17)
    assert s.get_game(game_id)["home_score"] == 24
    s.remove_game(game_id)
    with pytest.raises(KeyError):
        s.remove_game(game_id)
