"""Hidden tests for the initial quiz_rounds spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with quiz.py importable, e.g. in the sandbox):
    python -m pytest private/test_quiz_initial.py
"""

import pytest
from quiz import Quiz, QuizError


@pytest.fixture
def quiz():
    q = Quiz()
    for name in ["music", "sport", "film"]:
        q.add_round(name)
    for question in ["m1", "m2", "m3"]:
        q.add_question("music", question)
    for question in ["s1", "s2"]:
        q.add_question("sport", question)
    return q


def state(q):
    """Every round in order with its questions, to check that a failed call
    changed nothing."""
    return [(r, q.get_questions(r)) for r in q.get_rounds()]


# --- rounds -------------------------------------------------------------------


def test_a_new_round_is_empty():
    q = Quiz()
    q.add_round("music")
    assert q.get_questions("music") == []
    assert q.get_rounds() == ["music"]


def test_rounds_are_listed_in_the_order_added():
    q = Quiz()
    for name in ["sport", "art", "music"]:
        q.add_round(name)
    assert q.get_rounds() == ["sport", "art", "music"]


def test_adding_a_round_name_in_use_is_rejected(quiz):
    before = state(quiz)
    with pytest.raises(QuizError):
        quiz.add_round("sport")
    assert state(quiz) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda q: q.add_question("art", "a1"),
        lambda q: q.move_question("m1", "art"),
        lambda q: q.merge_rounds("art", "sport"),
        lambda q: q.merge_rounds("sport", "art"),
        lambda q: q.drop_round("art"),
        lambda q: q.get_questions("art"),
        lambda q: q.remove_question("x9"),
        lambda q: q.move_question("x9", "sport"),
    ],
)
def test_unknown_rounds_and_questions_raise_key_error(quiz, call):
    before = state(quiz)
    with pytest.raises(KeyError):
        call(quiz)
    assert state(quiz) == before


# --- questions ----------------------------------------------------------------


def test_questions_keep_the_order_they_were_added_in(quiz):
    quiz.add_question("film", "f2")
    quiz.add_question("film", "f1")
    quiz.add_question("music", "m0")
    assert quiz.get_questions("film") == ["f2", "f1"]
    assert quiz.get_questions("music") == ["m1", "m2", "m3", "m0"]


def test_remove_question_keeps_the_order_of_the_others(quiz):
    quiz.remove_question("m2")
    assert quiz.get_questions("music") == ["m1", "m3"]
    assert quiz.get_questions("sport") == ["s1", "s2"]


def test_a_removed_question_is_gone(quiz):
    quiz.remove_question("s1")
    before = state(quiz)
    with pytest.raises(KeyError):
        quiz.remove_question("s1")
    with pytest.raises(KeyError):
        quiz.move_question("s1", "film")
    assert state(quiz) == before


def test_a_removed_id_can_be_added_again_in_any_round(quiz):
    quiz.remove_question("m1")
    quiz.add_question("film", "m1")
    assert quiz.get_questions("film") == ["m1"]
    assert quiz.get_questions("music") == ["m2", "m3"]


def test_move_question_puts_it_at_the_end_of_the_other_round(quiz):
    quiz.move_question("m2", "sport")
    assert quiz.get_questions("music") == ["m1", "m3"]
    assert quiz.get_questions("sport") == ["s1", "s2", "m2"]


def test_a_moved_question_can_be_moved_again(quiz):
    quiz.move_question("m1", "film")
    quiz.move_question("m1", "sport")
    quiz.remove_question("m1")
    assert quiz.get_questions("film") == []
    assert quiz.get_questions("sport") == ["s1", "s2"]


# --- merging rounds -----------------------------------------------------------


def test_merge_rounds_appends_the_questions_in_order(quiz):
    quiz.add_question("film", "f1")
    assert quiz.merge_rounds("music", "film") == 3
    assert quiz.get_questions("film") == ["f1", "m1", "m2", "m3"]
    assert quiz.get_rounds() == ["sport", "film"]


def test_merging_into_a_round_keeps_the_other_rounds(quiz):
    quiz.add_question("film", "f1")
    assert quiz.merge_rounds("sport", "film") == 2
    assert quiz.get_questions("film") == ["f1", "s1", "s2"]
    assert quiz.get_questions("music") == ["m1", "m2", "m3"]
    assert quiz.get_rounds() == ["music", "film"]


def test_merging_an_empty_round_moves_nothing(quiz):
    assert quiz.merge_rounds("film", "sport") == 0
    assert quiz.get_rounds() == ["music", "sport"]
    assert quiz.get_questions("sport") == ["s1", "s2"]


def test_merging_a_round_into_itself_raises(quiz):
    before = state(quiz)
    with pytest.raises(ValueError):
        quiz.merge_rounds("music", "music")
    assert state(quiz) == before


# --- dropping rounds ----------------------------------------------------------


def test_drop_round_removes_the_round_and_its_questions(quiz):
    assert quiz.drop_round("music") == 3
    assert quiz.get_rounds() == ["sport", "film"]
    assert quiz.get_questions("sport") == ["s1", "s2"]
    with pytest.raises(KeyError):
        quiz.move_question("m1", "sport")


def test_the_ids_of_a_dropped_round_are_free(quiz):
    quiz.drop_round("music")
    quiz.add_question("film", "m2")
    quiz.add_question("sport", "m1")
    assert quiz.get_questions("film") == ["m2"]
    assert quiz.get_questions("sport") == ["s1", "s2", "m1"]


def test_dropping_an_empty_round_removes_nothing_else(quiz):
    assert quiz.drop_round("film") == 0
    assert quiz.get_rounds() == ["music", "sport"]


# --- rounds that are gone -----------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda q: q.add_question("sport", "x1"),
        lambda q: q.move_question("m1", "sport"),
        lambda q: q.merge_rounds("sport", "film"),
        lambda q: q.merge_rounds("music", "sport"),
        lambda q: q.drop_round("sport"),
        lambda q: q.get_questions("sport"),
    ],
)
@pytest.mark.parametrize("how", ["merged", "dropped"])
def test_a_round_merged_away_or_dropped_is_not_in_use(quiz, how, call):
    if how == "merged":
        quiz.merge_rounds("sport", "film")
    else:
        quiz.drop_round("sport")
    before = state(quiz)
    with pytest.raises(KeyError):
        call(quiz)
    assert state(quiz) == before


def test_a_name_that_is_gone_can_be_added_again_at_the_end(quiz):
    quiz.merge_rounds("music", "film")
    quiz.drop_round("sport")
    quiz.add_round("music")
    quiz.add_round("sport")
    assert quiz.get_rounds() == ["film", "music", "sport"]
    assert quiz.get_questions("music") == []
    assert quiz.get_questions("sport") == []
    assert quiz.get_questions("film") == ["m1", "m2", "m3"]


def test_the_other_rounds_keep_their_order(quiz):
    quiz.add_round("art")
    quiz.merge_rounds("sport", "art")
    quiz.drop_round("music")
    assert quiz.get_rounds() == ["film", "art"]


# --- general ------------------------------------------------------------------


def test_quizzes_do_not_share_rounds():
    first, second = Quiz(), Quiz()
    first.add_round("music")
    first.add_question("music", "m1")
    second.add_round("music")
    assert second.get_questions("music") == []
    second.add_question("music", "m1")
    assert first.get_questions("music") == ["m1"]
