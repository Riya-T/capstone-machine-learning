"""Public checks for the c_limit change (round limits). Shown to the
editor, never to the writer.

Usage (with quiz.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/public/test_limit_public.py
"""

import pytest
from quiz import Quiz, RoundFull


@pytest.fixture
def quiz():
    q = Quiz()
    q.add_round("music")
    q.add_round("sport")
    return q


def test_a_new_round_has_no_limit(quiz):
    assert quiz.get_limit("music") is None
    quiz.set_limit("music", 2)
    assert quiz.get_limit("music") == 2


def test_adding_past_the_limit_raises(quiz):
    quiz.set_limit("music", 2)
    quiz.add_question("music", "m1")
    quiz.add_question("music", "m2")
    with pytest.raises(RoundFull):
        quiz.add_question("music", "m3")
    assert quiz.get_questions("music") == ["m1", "m2"]
