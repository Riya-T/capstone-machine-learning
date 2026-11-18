"""Public checks for quiz.py.

Usage (with quiz.py importable, e.g. in the sandbox):
    python -m pytest public/test_quiz_public.py
"""

import pytest
from quiz import Quiz, QuizError


@pytest.fixture
def quiz():
    q = Quiz()
    q.add_round("music")
    q.add_round("sport")
    for question in ["m1", "m2", "m3"]:
        q.add_question("music", question)
    q.add_question("sport", "s1")
    return q


def test_questions_and_rounds_keep_the_order_added(quiz):
    assert quiz.get_rounds() == ["music", "sport"]
    assert quiz.get_questions("music") == ["m1", "m2", "m3"]


def test_a_round_name_in_use_is_rejected(quiz):
    with pytest.raises(QuizError):
        quiz.add_round("sport")
    assert quiz.get_rounds() == ["music", "sport"]
    assert quiz.get_questions("sport") == ["s1"]


def test_a_moved_question_goes_to_the_end(quiz):
    quiz.move_question("m1", "sport")
    assert quiz.get_questions("music") == ["m2", "m3"]
    assert quiz.get_questions("sport") == ["s1", "m1"]


def test_a_removed_id_can_be_added_again(quiz):
    quiz.remove_question("m2")
    assert quiz.get_questions("music") == ["m1", "m3"]
    quiz.add_question("sport", "m2")
    assert quiz.get_questions("sport") == ["s1", "m2"]


def test_merge_rounds_appends_and_removes_the_source(quiz):
    assert quiz.merge_rounds("music", "sport") == 3
    assert quiz.get_rounds() == ["sport"]
    assert quiz.get_questions("sport") == ["s1", "m1", "m2", "m3"]
    with pytest.raises(KeyError):
        quiz.get_questions("music")


def test_drop_round_removes_it_with_its_questions(quiz):
    assert quiz.drop_round("sport") == 1
    assert quiz.get_rounds() == ["music"]
    with pytest.raises(KeyError):
        quiz.remove_question("s1")
