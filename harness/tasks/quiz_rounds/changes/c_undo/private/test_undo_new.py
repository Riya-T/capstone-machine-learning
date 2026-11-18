"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with quiz.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
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
    q.add_question("sport", "s1")
    return q


def state(q):
    return [(r, q.get_questions(r)) for r in q.get_rounds()]


# --- each call can be undone ------------------------------------------------


def test_undoing_remove_question_puts_it_back_in_its_old_place(quiz):
    before = state(quiz)
    quiz.remove_question("m2")
    quiz.undo()
    assert state(quiz) == before
    assert quiz.get_questions("music") == ["m1", "m2", "m3"]


def test_a_question_brought_back_can_be_used_again(quiz):
    quiz.remove_question("m1")
    quiz.undo()
    quiz.move_question("m1", "film")
    assert quiz.get_questions("film") == ["m1"]
    quiz.remove_question("m1")
    assert quiz.get_questions("music") == ["m2", "m3"]


def test_undoing_move_question_puts_it_back_in_its_old_place(quiz):
    before = state(quiz)
    quiz.move_question("m1", "sport")
    quiz.undo()
    assert state(quiz) == before
    assert quiz.get_questions("sport") == ["s1"]


def test_one_undo_takes_back_a_whole_merge(quiz):
    quiz.add_question("film", "f1")
    before = state(quiz)
    assert quiz.merge_rounds("music", "film") == 3
    quiz.undo()
    assert state(quiz) == before
    assert quiz.get_rounds() == ["music", "sport", "film"]
    assert quiz.get_questions("film") == ["f1"]


def test_questions_of_a_round_brought_back_belong_to_it_again(quiz):
    quiz.merge_rounds("music", "sport")
    quiz.undo()
    quiz.move_question("m2", "sport")
    assert quiz.get_questions("sport") == ["s1", "m2"]
    assert quiz.get_questions("music") == ["m1", "m3"]


def test_one_undo_brings_back_a_dropped_round_with_its_questions(quiz):
    before = state(quiz)
    assert quiz.drop_round("music") == 3
    quiz.undo()
    assert state(quiz) == before
    assert quiz.get_rounds() == ["music", "sport", "film"]
    quiz.remove_question("m3")
    assert quiz.get_questions("music") == ["m1", "m2"]


def test_a_round_brought_back_keeps_its_place_in_the_list(quiz):
    quiz.add_round("art")
    quiz.merge_rounds("sport", "art")
    assert quiz.get_rounds() == ["music", "film", "art"]
    quiz.undo()
    assert quiz.get_rounds() == ["music", "sport", "film", "art"]
    quiz.drop_round("sport")
    quiz.undo()
    assert quiz.get_rounds() == ["music", "sport", "film", "art"]
    assert quiz.get_questions("sport") == ["s1"]


def test_a_round_brought_back_is_in_use_again(quiz):
    quiz.drop_round("sport")
    quiz.undo()
    with pytest.raises(QuizError):
        quiz.add_round("sport")
    quiz.add_question("sport", "s2")
    assert quiz.get_questions("sport") == ["s1", "s2"]


def test_merging_or_dropping_an_empty_round_can_be_undone(quiz):
    assert quiz.merge_rounds("film", "sport") == 0
    quiz.undo()
    assert quiz.get_rounds() == ["music", "sport", "film"]
    assert quiz.drop_round("film") == 0
    quiz.undo()
    assert quiz.get_rounds() == ["music", "sport", "film"]
    assert quiz.get_questions("film") == []


def test_undoing_add_round_removes_it_and_frees_the_name(quiz):
    quiz.add_round("art")
    quiz.undo()
    assert quiz.get_rounds() == ["music", "sport", "film"]
    with pytest.raises(KeyError):
        quiz.get_questions("art")
    quiz.add_round("art")
    assert quiz.get_rounds() == ["music", "sport", "film", "art"]


def test_undoing_add_question_removes_it_and_frees_the_id(quiz):
    quiz.add_question("film", "f1")
    quiz.undo()
    assert quiz.get_questions("film") == []
    with pytest.raises(KeyError):
        quiz.remove_question("f1")
    quiz.add_question("sport", "f1")
    assert quiz.get_questions("sport") == ["s1", "f1"]


def test_undo_through_a_name_that_was_dropped_and_added_again(quiz):
    quiz.add_round("art")
    quiz.add_question("art", "a1")
    quiz.drop_round("art")
    quiz.add_round("art")  # a new, empty art
    quiz.add_question("art", "a2")
    quiz.undo()  # a2
    quiz.undo()  # the new art
    assert quiz.get_rounds() == ["music", "sport", "film"]
    quiz.undo()  # the drop: the old art comes back with a1
    assert quiz.get_rounds() == ["music", "sport", "film", "art"]
    assert quiz.get_questions("art") == ["a1"]
    quiz.undo()  # a1
    quiz.undo()  # the first art
    assert quiz.get_rounds() == ["music", "sport", "film"]


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    q = Quiz()
    calls = [
        lambda: q.add_round("music"),
        lambda: q.add_round("sport"),
        lambda: q.add_question("music", "m1"),
        lambda: q.add_question("sport", "s1"),
        lambda: q.add_question("music", "m2"),
        lambda: q.add_question("music", "m3"),
        lambda: q.add_round("film"),
        lambda: q.move_question("m1", "film"),
        lambda: q.remove_question("m2"),
        lambda: q.add_question("film", "m2"),
        lambda: q.merge_rounds("music", "sport"),
        lambda: q.add_round("art"),
        lambda: q.add_question("art", "a1"),
        lambda: q.drop_round("film"),
        lambda: q.merge_rounds("sport", "art"),
    ]
    states = [state(q)]
    for call in calls:
        call()
        states.append(state(q))
    assert q.get_rounds() == ["art"]
    assert q.get_questions("art") == ["a1", "s1", "m3"]
    for expected in reversed(states[:-1]):
        q.undo()
        assert state(q) == expected
    with pytest.raises(QuizError):
        q.undo()
    assert q.get_rounds() == []


def test_failed_calls_are_not_recorded(quiz):
    quiz.add_question("film", "f1")
    for call in (
        lambda: quiz.add_round("music"),
        lambda: quiz.add_question("art", "a1"),
        lambda: quiz.remove_question("x9"),
        lambda: quiz.move_question("x9", "sport"),
        lambda: quiz.move_question("m1", "art"),
        lambda: quiz.merge_rounds("music", "music"),
        lambda: quiz.drop_round("art"),
    ):
        with pytest.raises((QuizError, KeyError, ValueError)):
            call()
    quiz.undo()  # f1
    assert quiz.get_questions("film") == []
    assert quiz.get_questions("music") == ["m1", "m2", "m3"]


def test_get_calls_are_not_recorded(quiz):
    quiz.add_question("film", "f1")
    quiz.get_questions("film")
    quiz.get_rounds()
    quiz.undo()
    assert quiz.get_questions("film") == []
    assert quiz.get_questions("sport") == ["s1"]


def test_there_is_no_redo():
    q = Quiz()
    q.add_round("music")
    q.add_question("music", "m1")
    q.undo()
    q.undo()
    assert q.get_rounds() == []
    with pytest.raises(QuizError):
        q.undo()


def test_new_calls_after_an_undo_are_undone_first(quiz):
    quiz.add_question("film", "f1")
    quiz.undo()
    quiz.add_question("film", "f2")
    quiz.undo()
    assert quiz.get_questions("film") == []
    quiz.undo()  # s1 added in the fixture
    assert quiz.get_questions("sport") == []
    assert quiz.get_questions("music") == ["m1", "m2", "m3"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    q = Quiz()
    with pytest.raises(QuizError):
        q.undo()
    q.add_round("music")
    q.undo()
    with pytest.raises(QuizError):
        q.undo()
    assert q.get_rounds() == []
    q.add_round("music")
    q.add_question("music", "m1")
    assert q.get_questions("music") == ["m1"]


def test_the_whole_fixture_can_be_undone(quiz):
    for _ in range(7):
        quiz.undo()
    assert quiz.get_rounds() == []
    with pytest.raises(QuizError):
        quiz.undo()
