"""Hidden tests for the c_move_many change (moving several questions in one
call). Never shown to the writer or the editor.

Usage (with quiz.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move_many/private/test_move_many_new.py
"""

import pytest
from quiz import Quiz


@pytest.fixture
def quiz():
    q = Quiz()
    for name in ["music", "sport", "film"]:
        q.add_round(name)
    for question in ["m1", "m2", "m3"]:
        q.add_question("music", question)
    for question in ["s1", "s2"]:
        q.add_question("sport", question)
    q.add_question("film", "f1")
    return q


def state(q):
    return [(r, q.get_questions(r)) for r in q.get_rounds()]


# --- moving -------------------------------------------------------------------


def test_questions_from_several_rounds_go_to_the_end_in_list_order(quiz):
    assert quiz.move_questions(["s2", "m1", "m3"], "film") == 3
    assert quiz.get_questions("film") == ["f1", "s2", "m1", "m3"]
    assert quiz.get_questions("music") == ["m2"]
    assert quiz.get_questions("sport") == ["s1"]


def test_the_list_order_is_kept_not_the_round_order(quiz):
    quiz.move_questions(["m3", "m2", "m1"], "sport")
    assert quiz.get_questions("sport") == ["s1", "s2", "m3", "m2", "m1"]


def test_a_round_that_loses_every_question_stays_empty(quiz):
    assert quiz.move_questions(["f1", "s1", "s2"], "music") == 3
    assert quiz.get_rounds() == ["music", "sport", "film"]
    assert quiz.get_questions("sport") == []
    assert quiz.get_questions("film") == []
    assert quiz.get_questions("music") == ["m1", "m2", "m3", "f1", "s1", "s2"]


def test_a_list_of_one_question_works_like_move_question(quiz):
    assert quiz.move_questions(["m2"], "film") == 1
    assert quiz.get_questions("film") == ["f1", "m2"]
    assert quiz.get_questions("music") == ["m1", "m3"]


def test_moved_questions_belong_to_their_new_round(quiz):
    quiz.move_questions(["m1", "s1"], "film")
    quiz.remove_question("m1")
    quiz.move_question("s1", "music")
    assert quiz.get_questions("film") == ["f1"]
    assert quiz.get_questions("music") == ["m2", "m3", "s1"]
    assert quiz.drop_round("film") == 1


# --- all or nothing -----------------------------------------------------------


def test_an_unknown_id_stops_the_whole_call(quiz):
    before = state(quiz)
    with pytest.raises(KeyError):
        quiz.move_questions(["m1", "s1", "x9"], "film")
    assert state(quiz) == before


def test_an_unknown_round_moves_nothing(quiz):
    before = state(quiz)
    with pytest.raises(KeyError):
        quiz.move_questions(["m1", "s1"], "art")
    assert state(quiz) == before


def test_a_question_already_in_the_round_stops_the_whole_call(quiz):
    before = state(quiz)
    with pytest.raises(ValueError):
        quiz.move_questions(["m1", "s2", "f1"], "film")
    assert state(quiz) == before


def test_a_question_named_twice_stops_the_whole_call(quiz):
    before = state(quiz)
    with pytest.raises(ValueError):
        quiz.move_questions(["m1", "s1", "m1"], "film")
    assert state(quiz) == before


def test_an_empty_list_is_rejected(quiz):
    before = state(quiz)
    with pytest.raises(ValueError):
        quiz.move_questions([], "film")
    assert state(quiz) == before


def test_a_failed_call_can_be_retried_without_the_problem(quiz):
    with pytest.raises(ValueError):
        quiz.move_questions(["m2", "f1"], "film")
    assert quiz.move_questions(["m2"], "film") == 1
    assert quiz.get_questions("film") == ["f1", "m2"]
    assert quiz.get_questions("music") == ["m1", "m3"]


def test_a_removed_question_cannot_be_moved(quiz):
    quiz.remove_question("s1")
    before = state(quiz)
    with pytest.raises(KeyError):
        quiz.move_questions(["m1", "s1"], "film")
    assert state(quiz) == before
