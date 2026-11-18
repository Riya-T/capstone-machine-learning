"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with quiz.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from quiz import Quiz, QuizError


@pytest.fixture
def quiz():
    q = Quiz()
    q.add_round("music")
    q.add_round("sport")
    return q


def test_undo_takes_back_the_last_added_question(quiz):
    quiz.add_question("music", "m1")
    quiz.add_question("music", "m2")
    quiz.undo()
    assert quiz.get_questions("music") == ["m1"]
    quiz.undo()
    assert quiz.get_questions("music") == []


def test_undo_takes_back_a_move(quiz):
    quiz.add_question("music", "m1")
    quiz.move_question("m1", "sport")
    quiz.undo()
    assert quiz.get_questions("music") == ["m1"]
    assert quiz.get_questions("sport") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(QuizError):
        Quiz().undo()
