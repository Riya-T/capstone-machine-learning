"""Public checks for the c_move_many change (moving several questions in
one call). Shown to the editor, never to the writer.

Usage (with quiz.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move_many/public/test_move_many_public.py
"""

import pytest
from quiz import Quiz


@pytest.fixture
def quiz():
    q = Quiz()
    q.add_round("music")
    q.add_round("sport")
    for question in ["m1", "m2", "m3"]:
        q.add_question("music", question)
    q.add_question("sport", "s1")
    return q


def test_move_questions_moves_them_in_the_list_order(quiz):
    assert quiz.move_questions(["m3", "m1"], "sport") == 2
    assert quiz.get_questions("sport") == ["s1", "m3", "m1"]
    assert quiz.get_questions("music") == ["m2"]


def test_one_unknown_id_stops_the_whole_call(quiz):
    with pytest.raises(KeyError):
        quiz.move_questions(["m1", "x9"], "sport")
    assert quiz.get_questions("music") == ["m1", "m2", "m3"]
    assert quiz.get_questions("sport") == ["s1"]
